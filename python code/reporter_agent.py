"""
python code/reporter_agent.py
────────────────────────────────────────────────────────────────────────────
Agente Reporter de Sostenibilidad
  · Recibe el dict de KPIs del analyst_agent
  · Genera informe_browser.html  → para abrir en el navegador
  · Genera informe_esg_XXXX.pdf  → para descargar
────────────────────────────────────────────────────────────────────────────
"""

import json
import os
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

TEMPLATE_DIR = Path(__file__).parent.parent / "plantilla_informes"
BROWSER_TPL  = "informe_browser.html"
PDF_TPL      = "informe_pdf.html"

OUTPUT_DIR = Path(os.getenv(
    "ESG_REPORTS_DIR",
    r"/Users/davidsantossalvador/Desktop/ESG_demo/test_2/reports"
))


def generate_report(kpis: dict, tracker=None) -> dict:
    """
    Genera HTML + PDF a partir del dict de KPIs.
    Si se pasa un tracker, mide la huella local de esta fase.
    Devuelve: { "html": "/ruta/...", "pdf": "/ruta/..." }
    """
    context = _build_context(kpis)
    period  = kpis["period"]

    html_path = _render_and_save_html(context, period)
    pdf_path  = _render_and_save_pdf(context, period)

    print(f"✅ HTML: {html_path}")
    print(f"✅ PDF : {pdf_path}")

    # La fase PDF no consume tokens API — solo cómputo local
    if tracker:
        tracker._last_input_tokens  = 0
        tracker._last_output_tokens = 0

    return {"html": str(html_path), "pdf": str(pdf_path)}


def _build_context(kpis: dict) -> dict:
    k = kpis["kpis"]

    agua = k["agua"].copy()
    if "total_m3" in agua and "total_litros" not in agua:
        agua["total_litros"] = agua.pop("total_m3")

    def clean(d: dict) -> dict:
        return {key: (val if val is not None else 0) for key, val in d.items()}

    return {
        "period":       kpis["period"],
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "summary":      kpis["executive_summary"],
        "consumo":      SimpleNamespace(**clean(k["consumo_electrico"])),
        "agua":         SimpleNamespace(**clean(agua)),
        "residuos":     SimpleNamespace(**clean(k["residuos"])),
    }


def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False
    )


def _render_and_save_html(context: dict, period: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html_str  = _get_env().get_template(BROWSER_TPL).render(**context)
    safe      = period.replace(" ", "_").replace("/", "-")
    html_path = OUTPUT_DIR / f"informe_esg_{safe}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    return html_path


def _render_and_save_pdf(context: dict, period: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html_str = _get_env().get_template(PDF_TPL).render(**context)
    safe     = period.replace(" ", "_").replace("/", "-")
    pdf_path = OUTPUT_DIR / f"informe_esg_{safe}.pdf"
    with open(pdf_path, "wb") as f:
        result = pisa.CreatePDF(html_str, dest=f)
    if result.err:
        raise RuntimeError(f"xhtml2pdf error: {result.err}")
    return pdf_path


if __name__ == "__main__":
    mock_kpis = {
        "period": "2024",
        "kpis": {
            "consumo_electrico": {
                "total_kwh": 358997.58, "autoconsumo_kwh": 223620.70,
                "autoconsumo_pct": 62.29, "trend": "mejora",
                "interpretation": "El consumo eléctrico se redujo un 16,6% respecto a 2023."
            },
            "agua": {
                "total_litros": 3020, "trend": "estable",
                "interpretation": "Consumo hídrico de 3.020 litros sin referencia previa."
            },
            "residuos": {
                "total_tons": 15.82, "recycling_pct": 99.3, "trend": "mejora",
                "interpretation": "Tasa de reciclaje del 99,3%."
            }
        },
        "executive_summary": "Resumen de prueba para 2024."
    }
    paths = generate_report(mock_kpis)
    print(f"HTML → {paths['html']}")
    print(f"PDF  → {paths['pdf']}")