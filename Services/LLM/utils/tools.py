"""Herramientas para usar con el modelo LLM"""

import asyncio
from typing import Dict, Any, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import json
from motor.motor_asyncio import AsyncIOMotorDatabase

class ProductSearchInput(BaseModel):
    """Input schema para la herramienta de búsqueda de productos"""
    query: str = Field(description="Término de búsqueda para productos")
    max_results: int = Field(default=5, description="Número máximo de resultados")


class ProductSearchTool(BaseTool):
    """Herramienta para buscar productos en la base de datos"""
    name: str = "product_search"
    description: str = (
        "Busca productos en la base de datos por nombre. "
        "Útil para encontrar productos específicos."
    )
    args_schema: type[BaseModel] = ProductSearchInput
    db: AsyncIOMotorDatabase = None
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__()
        self.db = db
    
    async def _arun(self, query: str, max_results: int = 5) -> str:
        """Ejecutar la búsqueda de productos de forma asíncrona"""
        try:
            # Buscar productos que contengan la query en el nombre (case insensitive)
            cursor = self.db.products.find(
                {"name": {"$regex": query, "$options": "i"}}
            ).limit(max_results)
            
            products = await cursor.to_list(max_results)
            
            if not products:
                return f"No se encontraron productos para '{query}'"
            
            # Formatear resultados
            results = []
            for product in products:
                results.append({
                    "name": product["name"],
                    "price": f"${product['unit_price']}",
                    "stock": product["stock"]
                })
            
            return json.dumps(results, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"Error buscando productos: {str(e)}"
    
    def _run(self, query: str, max_results: int = 5) -> str:
        """Versión síncrona (no usada en async context)"""
        return "Esta herramienta requiere contexto asíncrono"


class PriceCalculatorInput(BaseModel):
    """Input schema para la calculadora de precios"""
    products: List[Dict[str, Any]] = Field(
        description="Lista de productos con cantidades. Cada ítem debe incluir name, price y quantity."
    )
    discount_percent: float = Field(
        default=0.0,
        description="Porcentaje de descuento a aplicar sobre el subtotal (0-100)."
    )


class PriceCalculatorTool(BaseTool):
    """Herramienta para calcular precios totales con descuentos"""
    name: str = "price_calculator"
    description: str = (
        "Calcula el precio final de una compra. "
        "Úsala cuando el usuario pida sumar productos, calcular totales, "
        "aplicar descuentos o hacer un presupuesto. "
        "Requiere una lista de productos con 'name', 'price' (número) y 'quantity'. "
        "Puede incluir 'discount_percent' para aplicar un descuento. "
        "Retorna un JSON estructurado con el desglose de subtotales y el total final."
    )
    args_schema: type[BaseModel] = PriceCalculatorInput

    async def _arun(
        self,
        products: List[Dict[str, Any]],
        discount_percent: float = 0.0
    ) -> str:
        """Calcular el precio total de forma asíncrona"""
        try:
            total = 0.0
            breakdown = []

            for item in products:
                name = item.get("name", "Producto sin nombre")
                raw_price = item.get("price", 0)

                # Normalizar price a float aunque venga como string tipo "$ 1.234,56"
                if isinstance(raw_price, str):
                    raw_price = (
                        raw_price.replace("$", "")
                        .replace(",", "")
                        .strip()
                    )
                price = float(raw_price)

                quantity = int(item.get("quantity", 1))

                subtotal = price * quantity
                total += subtotal

                breakdown.append({
                    "product": name,
                    "price": f"{price:.2f}",
                    "quantity": quantity,
                    "subtotal": f"{subtotal:.2f}",
                })

            # Aplicar descuento si existe
            discount_amount = 0.0
            if discount_percent > 0:
                discount_amount = total * (discount_percent / 100)
                total -= discount_amount

            result = {
                "breakdown": breakdown,
                "subtotal": f"{total + discount_amount:.2f}",
                "discount": f"{discount_percent}%" if discount_percent > 0 else "0%",
                "discount_amount": f"{discount_amount:.2f}",
                "total": f"{total:.2f}",
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return f"Error calculando precios: {str(e)}"

    def _run(
        self,
        products: List[Dict[str, Any]],
        discount_percent: float = 0.0
    ) -> str:
        """Versión síncrona requerida por BaseTool (no usada en contexto async)"""
        return "Esta herramienta requiere contexto asíncrono (usar ainvoke/_arun)."

# Función para obtener todas las herramientas disponibles
def get_tools(db: AsyncIOMotorDatabase) -> List[BaseTool]:
    """Retorna lista de todas las herramientas disponibles"""
    return [
        ProductSearchTool(db),
        PriceCalculatorTool()
    ]