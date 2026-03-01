"""
data/check_db.py
────────────────────────────────────────────────────────────────────────────
Script de verificación: comprueba que la base de datos DuckDB es accesible
y muestra el esquema + conteo de filas de cada tabla.

Uso:
    python data/check_db.py
    ESG_DB_PATH=/ruta/alternativa.duckdb python data/check_db.py
────────────────────────────────────────────────────────────────────────────
"""

import os
import duckdb

DB_PATH = os.getenv(
    "ESG_DB_PATH",
    r"/Users/davidsantossalvador/Desktop/ESG_demo/test_2/data/esg_database.duckdb"
)

def check():
    print(f"📂 Conectando a: {DB_PATH}\n")
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return

    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    print(f"✅ Tablas encontradas: {tables}\n")
    print("─" * 60)

    for t in tables:
        # Esquema
        cols = con.execute(f"DESCRIBE {t}").fetchdf()
        count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

        print(f"\n📋 Tabla: {t}  ({count} filas)")
        for _, row in cols.iterrows():
            print(f"   {row['column_name']:<35} {row['column_type']}")

        # Muestra de 2 filas
        sample = con.execute(f"SELECT * FROM {t} LIMIT 2").fetchdf()
        print(f"\n   Muestra:")
        print(sample.to_string(index=False, max_colwidth=30))
        print("─" * 60)

    con.close()
    print("\n✅ Verificación completada.")

if __name__ == "__main__":
    check()
