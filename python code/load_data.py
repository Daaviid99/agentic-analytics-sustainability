"""
data/load_data.py
Convierte las hojas del Excel de sostenibilidad en tablas DuckDB.

Uso:
    python data/load_data.py
"""

import duckdb
import pandas as pd

# ── Rutas ─────────────────────────────────────────────────────────────────────

EXCEL_PATH = r"/Users/davidsantossalvador/Desktop/ESG_demo/test_2/excel_file/environment_data.xlsx"
DB_PATH    = r"/Users/davidsantossalvador/Desktop/ESG_demo/test_2/data/esg_database.duckdb"

# ── Leer hojas del Excel ──────────────────────────────────────────────────────

db_excel_consumo    = pd.read_excel(EXCEL_PATH, sheet_name='2. Consumo eléctrico', keep_default_na=True)
db_excel_autoconsumo = pd.read_excel(EXCEL_PATH, sheet_name='2b. Autoconsumo',     keep_default_na=True)
db_excel_agua       = pd.read_excel(EXCEL_PATH, sheet_name='3. Agua',              keep_default_na=True)
db_excel_residuos   = pd.read_excel(EXCEL_PATH, sheet_name='4. Residuos',          keep_default_na=True)

# ── Crear tablas en DuckDB ────────────────────────────────────────────────────

con = duckdb.connect(DB_PATH)

con.execute("CREATE OR REPLACE TABLE consumo_electrico AS SELECT * FROM db_excel_consumo")
con.execute("CREATE OR REPLACE TABLE autoconsumo       AS SELECT * FROM db_excel_autoconsumo")
con.execute("CREATE OR REPLACE TABLE agua              AS SELECT * FROM db_excel_agua")
con.execute("CREATE OR REPLACE TABLE residuos          AS SELECT * FROM db_excel_residuos")

# ── Verificar ─────────────────────────────────────────────────────────────────

print(con.execute("SHOW TABLES").fetchall())

con.close()