import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

CSV_PATH = os.getenv(
    "CSV_PATH",
    r"A:\drug-equivalents-app\data\Rejestr_Produktow_Leczniczych_calosciowy_stan_na_dzien_20260327 (1).csv"
)

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "drugs"
DB_USER = "drugs_user"
DB_PASSWORD = "drugs_pass"

def main() -> None:
    print("Wczytywanie CSV...")
    df = pd.read_csv(
        CSV_PATH,
        sep=";",
        dtype=str,
        encoding="utf-8"
    )

    df["source_file"] = os.path.basename(CSV_PATH)

    print(f"Wczytano {len(df)} rekordów z pliku.")

    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

    print("Łączenie z PostgreSQL...")
    engine = create_engine(connection_url)

    print("Import do tabeli medicinal_products_raw...")
    df.to_sql(
        "medicinal_products_raw",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )

    print(f"Zaimportowano {len(df)} rekordów do medicinal_products_raw")

if __name__ == "__main__":
    main()