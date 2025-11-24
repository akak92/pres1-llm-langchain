import asyncio
import logging
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import uvicorn

# Importaciones locales
from config import settings
from schemas import (
    ProductQuery, 
    ChatRequest, 
    ProductRecommendation, 
    ProductsResponse,
    ChatResponse,
    HealthResponse,
    BaseResponse
)

# Configurar logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# Variables globales
mongo_client = None
db = None
llm = None


async def initialize_services():
    """Inicializar servicios de MongoDB y Azure OpenAI"""
    global mongo_client, db, llm
    
    try:
        # Inicializar MongoDB
        mongo_client = AsyncIOMotorClient(settings.mongo_uri)
        db = mongo_client.store
        logger.info("✅ Conectado a MongoDB")
        
        # Inicializar Azure OpenAI con LangChain
        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_key,
            azure_deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_version,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        logger.info("✅ Conectado a Azure OpenAI GPT-4.1")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        raise


async def cleanup_services():
    """Limpiar servicios al cerrar la aplicación"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("🔒 Conexión MongoDB cerrada")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando servicios...")
    await initialize_services()
    yield
    # Shutdown
    logger.info("🔄 Cerrando servicios...")
    await cleanup_services()


# Inicializar FastAPI con lifespan
app = FastAPI(
    title="LLM Service with LangChain", 
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_model=BaseResponse)
async def root():
    """Endpoint raíz"""
    return BaseResponse(message="LLM Service with LangChain and Azure OpenAI GPT-4.1")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificar estado de los servicios"""
    try:
        # Verificar MongoDB - usar una operación simple en lugar de admin command
        await db.products.count_documents({})
        mongo_status = "healthy"
    except Exception as e:
        mongo_status = "unhealthy"
        logger.error(f"MongoDB health check failed: {e}")
    
    try:
        # Verificar Azure OpenAI
        test_response = await llm.ainvoke([HumanMessage(content="Hello")])
        llm_status = "healthy"
    except Exception as e:
        llm_status = "unhealthy"
        logger.error(f"Azure OpenAI health check failed: {e}")
    
    overall_status = "healthy" if mongo_status == "healthy" and llm_status == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        services={
            "mongodb": mongo_status,
            "azure_openai": llm_status
        }
    )


@app.get("/products", response_model=ProductsResponse)
async def get_products(limit: int = 10):
    """Obtener productos de la base de datos"""
    try:
        products = await db.products.find().limit(limit).to_list(limit)
        # Convertir ObjectId a string
        for product in products:
            product["_id"] = str(product["_id"])
        return ProductsResponse(products=products, count=len(products))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")


@app.post("/recommend", response_model=ProductRecommendation)
async def recommend_products(request: ProductQuery):
    """Recomendar productos usando LangChain y Azure OpenAI"""
    try:
        # Obtener productos de MongoDB
        products = await db.products.find().limit(20).to_list(20)
        
        # Preparar contexto de productos
        products_context = "\\n".join([
            f"- {p['name']}: ${p['unit_price']} (Stock: {p['stock']})"
            for p in products
        ])
        
        # Crear mensajes para LangChain
        system_message = SystemMessage(content=f"""
        Eres un asistente experto en recomendación de productos tecnológicos.
        Tu tarea es recomendar productos basándote en la consulta del usuario.
        
        Productos disponibles:
        {products_context}
        
        Proporciona recomendaciones específicas y justifica tu elección.
        Mantén un tono profesional pero amigable.
        """)
        
        human_message = HumanMessage(content=f"""
        El usuario pregunta: "{request.query}"
        
        Por favor, recomienda hasta {request.max_products} productos que mejor se adapten a esta consulta.
        Explica por qué estos productos son adecuados.
        """)
        
        # Obtener respuesta de Azure OpenAI
        response = await llm.ainvoke([system_message, human_message])
        
        # Filtrar productos relevantes (simplificado)
        filtered_products = products[:request.max_products]
        for product in filtered_products:
            product["_id"] = str(product["_id"])
        
        return ProductRecommendation(
            products=filtered_products,
            recommendation=response.content
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat general con Azure OpenAI usando LangChain"""
    try:
        messages = [
            SystemMessage(content="""
            Eres un asistente útil especializado en tecnología y productos electrónicos.
            Responde de manera clara, concisa y profesional.
            """),
            HumanMessage(content=request.message)
        ]
        
        if request.context:
            messages.insert(1, SystemMessage(content=f"Contexto adicional: {request.context}"))
        
        response = await llm.ainvoke(messages)
        
        return ChatResponse(
            response=response.content,
            model=settings.azure_openai_deployment
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en chat: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )