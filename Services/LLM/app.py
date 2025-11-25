import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import (
    HumanMessage,
)
import uvicorn

from utils import settings
from utils.prompts import CHAT_SYSTEM_PROMPT
from utils.tools import get_tools  # devuelve lista de BaseTool
from utils.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    BaseResponse,
)

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)


async def initialize_services(app: FastAPI) -> None:
    try:
        # --- MongoDB ---
        mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
        db: AsyncIOMotorDatabase = mongo_client.store
        logger.info("✅ Conectado a MongoDB")

        # --- LLM base (AzureChatOpenAI, sin bind_tools acá) ---
        llm = AzureChatOpenAI(
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            openai_api_key=settings.AZURE_OPENAI_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            openai_api_version=settings.AZURE_OPENAI_VERSION,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

        # --- Tools ---
        tools = get_tools(db)

        # --- Prompt del agente ---
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CHAT_SYSTEM_PROMPT),
                # por ahora no usamos historial, pero dejamos el placeholder
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                # donde el agente va a inyectar llamadas a tools
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        # --- Crear agente orientado a tools ---
        agent = create_tool_calling_agent(llm, tools, prompt)

        # --- AgentExecutor (sync + async) ---
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,  # opcional, pero útil para debug
        )

        # Guardar en app.state
        app.state.mongo_client = mongo_client
        app.state.db = db
        app.state.llm = llm          # para health check si querés
        app.state.tools = tools
        app.state.agent = agent_executor

        logger.info("✅ Agente con tools inicializado")
        logger.info("⚙️ Tools: %s", [t.name for t in tools])

    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        raise


async def cleanup_services(app: FastAPI) -> None:
    """Cerrar conexiones al apagar la app."""
    mongo_client = getattr(app.state, "mongo_client", None)
    if mongo_client:
        mongo_client.close()
        logger.info("🔒 Conexión MongoDB cerrada")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando servicios...")
    await initialize_services(app)
    try:
        yield
    finally:
        logger.info("🔄 Cerrando servicios...")
        await cleanup_services(app)


app = FastAPI(
    title="LLM Service with LangChain",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_model=BaseResponse)
async def root():
    return BaseResponse(
        message="LLM Service with LangChain and Azure OpenAI GPT-4.1"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    db: AsyncIOMotorDatabase = app.state.db
    llm = app.state.llm

    # --- Mongo ---
    try:
        await db.command("ping")
        mongo_status = "healthy"
    except Exception as e:
        mongo_status = "unhealthy"
        logger.error(f"MongoDB health check failed: {e}")

    # --- LLM ---
    try:
        test_resp = await llm.ainvoke([HumanMessage(content="Hello")])
        _ = test_resp.content  # fuerza acceso
        llm_status = "healthy"
    except Exception as e:
        llm_status = "unhealthy"
        logger.error(f"Azure OpenAI health check failed: {e}")

    overall_status = (
        "healthy" if mongo_status == "healthy" and llm_status == "healthy" else "unhealthy"
    )

    return HealthResponse(
        status=overall_status,
        services={
            "mongodb": mongo_status,
            "azure_openai": llm_status,
        },
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_AI(request: ChatRequest):
    """
    Chat general con LLM + herramientas usando AgentExecutor.
    """
    agent: AgentExecutor = app.state.agent

    try:
        result = await agent.ainvoke(
            {
                "input": request.message,
                "chat_history": [],
            }
        )
        # AgentExecutor devuelve un dict con key 'output'
        final_text = result.get("output", "")

        if not final_text:
            final_text = "No pude generar una respuesta para esta consulta."

        return ChatResponse(
            response=final_text,
            model=settings.AZURE_OPENAI_DEPLOYMENT,
        )

    except Exception as e:
        logger.exception("Error en /chat")
        raise HTTPException(status_code=500, detail=f"Error en chat: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
