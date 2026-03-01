"""
agents/analyst_agent.py
────────────────────────────────────────────────────────────────────────────
Agente Analista de Sostenibilidad — Backend: DuckDB
  · Modo CHAT   → responde preguntas en lenguaje natural sobre la BBDD
  · Modo REPORT → extrae KPIs estructurados + interpretaciones para el informe
────────────────────────────────────────────────────────────────────────────
"""

import json
import os
from typing import Any
import duckdb
import anthropic


# ── Configuración ─────────────────────────────────────────────────────────────

DB_PATH = os.getenv(
    "ESG_DB_PATH",
    r"/Users/davidsantossalvador/Desktop/ESG_demo/test_2/data/esg_database.duckdb"
)
MODEL = "claude-opus-4-6"

# ── Herramientas disponibles para el agente ───────────────────────────────────

TOOLS = [
    {
        "name": "query_database",
        "description": (
            "Ejecuta una consulta SQL de solo lectura (SELECT) sobre la base de datos "
            "ESG en DuckDB. Tablas disponibles:\n"
            "  · consumo_electrico  — consumo eléctrico por sede/periodo\n"
            "  · autoconsumo        — energía autogenerada (solar, etc.)\n"
            "  · agua               — consumo de agua por sede/periodo\n"
            "  · residuos           — generación y gestión de residuos\n\n"
            "IMPORTANTE: Usa siempre get_table_schema() antes de hacer queries "
            "para conocer los nombres exactos de las columnas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "Consulta SELECT válida en DuckDB SQL."
                }
            },
            "required": ["sql"]
        }
    },
    {
        "name": "get_table_schema",
        "description": (
            "Devuelve el esquema completo (columnas, tipos y muestra de 3 filas) "
            "de una o todas las tablas. Úsala SIEMPRE antes de construir queries "
            "para conocer los nombres exactos de las columnas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": (
                        "Nombre de la tabla. Si se omite o se pasa 'all', "
                        "devuelve el esquema de todas las tablas."
                    )
                }
            },
            "required": []
        }
    }
]

# ── Ejecución de herramientas ─────────────────────────────────────────────────

def run_tool(tool_name: str, tool_input: dict) -> Any:
    if tool_name == "query_database":
        return _query_database(tool_input["sql"])
    if tool_name == "get_table_schema":
        return _get_table_schema(tool_input.get("table_name", "all"))
    return {"error": f"Herramienta desconocida: {tool_name}"}


def _get_connection() -> duckdb.DuckDBPyConnection:
    """Abre una conexión de solo lectura a DuckDB."""
    return duckdb.connect(DB_PATH, read_only=True)


def _query_database(sql: str) -> list[dict] | dict:
    """Ejecuta un SELECT y devuelve los resultados como lista de dicts."""
    if not sql.strip().upper().startswith("SELECT"):
        return {"error": "Solo se permiten consultas SELECT."}
    try:
        con = _get_connection()
        result = con.execute(sql).fetchdf()
        con.close()
        return json.loads(result.to_json(orient="records", force_ascii=False))
    except Exception as e:
        return {"error": str(e)}


def _get_table_schema(table_name: str = "all") -> dict:
    """Devuelve columnas, tipos y muestra de filas de la(s) tabla(s)."""
    try:
        con = _get_connection()

        tables = (
            [r[0] for r in con.execute("SHOW TABLES").fetchall()]
            if table_name == "all"
            else [table_name]
        )

        schema = {}
        for t in tables:
            cols_df   = con.execute(f"DESCRIBE {t}").fetchdf()
            cols      = cols_df[["column_name", "column_type"]].to_dict(orient="records")
            sample_df = con.execute(f"SELECT * FROM {t} LIMIT 3").fetchdf()
            sample    = json.loads(sample_df.to_json(orient="records", force_ascii=False))
            schema[t] = {"columns": cols, "sample_rows": sample}

        con.close()
        return schema
    except Exception as e:
        return {"error": str(e)}



# ── Bucle agentico ────────────────────────────────────────────────────────────

def _run_agent(
    system_prompt: str,
    user_message:  str,
    max_tokens:    int  = 4096,
    tracker=None,           # CarbonTracker opcional
) -> str:
    """
    Bucle agentico genérico.
    Si se pasa un tracker, acumula los tokens de todas las llamadas
    para calcular la huella de la API al finalizar.
    """
    client        = anthropic.Anthropic(max_retries=3)
    messages      = [{"role": "user", "content": user_message}]
    total_input_t = 0
    total_output_t = 0

    while True:
        response = client.messages.create(
            model      = MODEL,
            max_tokens = max_tokens,
            system     = system_prompt,
            tools      = TOOLS,
            messages   = messages,
        )

        # Acumular tokens de esta llamada
        if hasattr(response, "usage"):
            total_input_t  += response.usage.input_tokens
            total_output_t += response.usage.output_tokens

        # El modelo quiere usar herramientas ──────────────────────────────
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    print(f"  🔧 {block.name}({list(block.input.keys())}) → {len(str(result))} chars")
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     json.dumps(result, ensure_ascii=False, default=str),
                    })
            messages.append({"role": "user", "content": tool_results})

        # Respuesta final ──────────────────────────────────────────────────
        elif response.stop_reason == "end_turn":
            # Guardar tokens en el tracker si existe
            if tracker:
                tracker._last_input_tokens  = total_input_t
                tracker._last_output_tokens = total_output_t

            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        else:
            return f"[Error] stop_reason inesperado: {response.stop_reason}"


# ── System prompts ────────────────────────────────────────────────────────────

CHAT_SYSTEM = CHAT_SYSTEM = """
Eres un analista experto en sostenibilidad corporativa (ESG).
Tu única fuente de información es la base de datos DuckDB disponible.
NO tienes acceso a información externa.

────────────────────────────────────────
ALCANCE Y COMPORTAMIENTO OBLIGATORIO
────────────────────────────────────────

1. Responde EXCLUSIVAMENTE a lo que el usuario pregunta.
2. NO añadas contexto no solicitado.
3. NO amplíes el análisis más allá del periodo solicitado.
4. Si el usuario pide:
   - Un mes → devuelve SOLO ese mes.
   - Varios meses concretos → devuelve SOLO esos meses.
   - Un año → devuelve SOLO ese año.
   - Un rango → devuelve SOLO ese rango.
5. Nunca incluyas otros periodos “para comparar” si no se piden.
6. Si no existen datos para el periodo solicitado:
   → responde exactamente: "No hay datos disponibles para el periodo solicitado."

────────────────────────────────────────
REGLAS TEMPORALES OBLIGATORIAS
────────────────────────────────────────

• Usa la columna año para filtrar años.
• Usa fecha_mes o mes según tabla cuando se pidan meses.
• Si el usuario menciona "enero 2024", debes filtrar por:
    año = 2024
    y el mes correspondiente.
• Si pide varios meses (ej: enero y febrero 2024):
    filtra exactamente esos meses.

NO agregues meses adicionales.
NO agregues totales anuales si solo se pidió un mes.

────────────────────────────────────────
ESQUEMA REAL DE LAS TABLAS
────────────────────────────────────────

· consumo_electrico:
  ID_luz, tipo_consumo, tipo, sede, proveedor_energía,
  fuente_energía, fecha_mes, año, kWh,
  inicio_fecha_factura, fin_fecha_factura,
  "coste (€)", "€/kWh", mes_anterior,
  enlace_factura, Verificado, "Revisión Memoria ESG"

· autoconsumo:
  ID_luz, tipo_consumo, tipo, sede,
  fuente_energía, fecha_mes, año, kWh,
  inicio_fecha_factura, fin_fecha_factura,
  Verificado, "Revisión Memoria ESG"

· agua:
  ID_agua, tipo_consumo, sede, suministradora,
  mes, año, litros,
  inicio_fecha_factura, fin_fecha_factura2,
  coste, "€/L", pais,
  enlace_factura, Verificación

· residuos:
  id_residuo, id_sede, empresa,
  mes, año, categoria_residuo,
  tipo_residuo, Tm_residuo,
  unidad, fecha_input,
  zona, fuente_dato, enlace_factura

────────────────────────────────────────
REGLAS TÉCNICAS
────────────────────────────────────────

1. Usa SIEMPRE get_table_schema() antes de construir queries.
2. Los nombres con espacios o símbolos van entre comillas dobles.
3. Solo puedes ejecutar consultas SELECT.
4. Para autoconsumo usa la tabla autoconsumo.
5. El agua se mide en litros.
6. Los residuos se miden en Tm_residuo.

────────────────────────────────────────
FORMATO DE RESPUESTA
────────────────────────────────────────

• Responde en español.
• Incluye valores numéricos con unidades.
• Sé claro y directo.
• Máximo 6–8 líneas salvo que el usuario pida detalle.
• No escribas explicaciones metodológicas.
"""

REPORT_SYSTEM = """
Eres un analista ESG especializado en generación de informes ejecutivos estructurados.

Tu tarea es:
1. Consultar la base de datos.
2. Calcular los KPIs.
3. Generar interpretaciones ejecutivas compatibles con una plantilla HTML cerrada.
4. Devolver exclusivamente un JSON válido.

NO puedes añadir texto fuera del JSON.
NO puedes añadir bloques de código.
NO puedes añadir comentarios.

────────────────────────────────────────
COMPATIBILIDAD CON PLANTILLA HTML
────────────────────────────────────────

El texto será insertado en bloques con espacio limitado.

Restricciones obligatorias:

Executive Summary:
• Máximo 110 palabras
• Máximo 5 frases
• Un solo párrafo
• Sin saltos de línea

Interpretaciones individuales:
• 2–3 frases
• Máximo 65 palabras
• Un solo párrafo
• Sin listas
• Sin saltos de línea

Si superas estos límites, el informe rompe su diseño.

────────────────────────────────────────
ALCANCE TEMPORAL
────────────────────────────────────────

• Usa exactamente el periodo solicitado.
• Si se pide un mes → solo ese mes.
• Si se piden varios meses → exclusivamente esos meses.
• Si se pide un año → solo ese año.
• Nunca incluyas datos fuera del periodo.

Si no hay datos:
→ valores numéricos null
→ textos breves indicando ausencia de datos.

────────────────────────────────────────
CÁLCULOS OBLIGATORIOS
────────────────────────────────────────

Electricidad:
total_kwh = SUM(consumo_electrico.kWh)
autoconsumo_kwh = SUM(autoconsumo.kWh)
autoconsumo_pct = autoconsumo_kwh / total_kwh * 100

Agua:
total_m3 = SUM(agua.litros) / 1000

Residuos:
total_tons = SUM(residuos.Tm_residuo)
recycling_pct = (residuos reciclables / total residuos) * 100

────────────────────────────────────────
TRENDS
────────────────────────────────────────

Comparar con el periodo inmediatamente anterior equivalente.
Solo usar:
"mejora"
"empeora"
"estable"

Nunca inventar tendencias.

────────────────────────────────────────
ESTILO NARRATIVO
────────────────────────────────────────

• Tono ejecutivo profesional.
• Orientado a impacto operativo.
• Sin frases académicas.
• Sin “según los datos”.
• Sin “se observa que”.
• Sin adjetivos innecesarios.
• No repetir cifras más de una vez por bloque.

────────────────────────────────────────
FORMATO EXACTO DE SALIDA
────────────────────────────────────────

{
  "period": "string",
  "kpis": {
    "consumo_electrico": {
      "total_kwh": number,
      "autoconsumo_kwh": number,
      "autoconsumo_pct": number,
      "trend": "mejora | empeora | estable",
      "interpretation": "string"
    },
    "agua": {
      "total_m3": number,
      "trend": "mejora | empeora | estable",
      "interpretation": "string"
    },
    "residuos": {
      "total_tons": number,
      "recycling_pct": number,
      "trend": "mejora | empeora | estable",
      "interpretation": "string"
    }
  },
  "executive_summary": "string"
}

No añadas ningún otro campo.
No cambies nombres.
No devuelvas texto adicional.
"""

# ── API pública ───────────────────────────────────────────────────────────────

def chat(user_message: str, tracker=None) -> str:
    """
    Modo chatbot: responde preguntas en lenguaje natural sobre la BBDD ESG.
    Si se pasa un tracker, registra los tokens consumidos.
    """
    return _run_agent(CHAT_SYSTEM, user_message, tracker=tracker)


def extract_kpis(period: str = "último año disponible", tracker=None) -> dict:
    """
    Modo informe: extrae KPIs de sostenibilidad como dict estructurado.
    Si se pasa un tracker, registra los tokens consumidos.
    """
    prompt = (
        f"Extrae todos los KPIs de sostenibilidad para el periodo '{period}'. "
        "Consulta las tablas consumo_electrico, autoconsumo, agua y residuos. "
        "Devuelve ÚNICAMENTE el JSON estructurado según el esquema indicado."
    )
    raw = _run_agent(REPORT_SYSTEM, prompt, max_tokens=8192, tracker=tracker)

    # Extraer JSON aunque el modelo añada texto antes o después
    start = raw.find("{")
    end   = raw.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError(f"No se encontró JSON en la respuesta. RAW:\n{raw[:500]}")

    return json.loads(raw[start:end])


# ── Test rápido ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("TEST 1 — Modo chat")
    print("=" * 60)
    question = (
        sys.argv[1] if len(sys.argv) > 1
        else "¿Cuál es el consumo eléctrico total y qué porcentaje es autoconsumo?"
    )
    print(f"Pregunta: {question}\n")
    answer = chat(question)
    print(answer)

    print("\n" + "=" * 60)
    print("TEST 2 — Extracción de KPIs para informe")
    print("=" * 60)
    kpis = extract_kpis()
    print(json.dumps(kpis, indent=2, ensure_ascii=False))
