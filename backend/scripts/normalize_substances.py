import re
from typing import List

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://drugs_user:drugs_pass@127.0.0.1:55432/drugs"

engine = create_engine(DATABASE_URL)

UNIT_PATTERNS = [
    r"\b\d+(?:[.,]\d+)?\s*mg\b",
    r"\b\d+(?:[.,]\d+)?\s*g\b",
    r"\b\d+(?:[.,]\d+)?\s*mcg\b",
    r"\b\d+(?:[.,]\d+)?\s*µg\b",
    r"\b\d+(?:[.,]\d+)?\s*ml\b",
    r"\b\d+(?:[.,]\d+)?\s*mg/ml\b",
    r"\b\d+(?:[.,]\d+)?\s*g/ml\b",
    r"\b\d+(?:[.,]\d+)?\s*%\b",
]

MULTISPACE_RE = re.compile(r"\s+")
PAREN_RE = re.compile(r"\([^)]*\)")
UNIT_RE = re.compile("|".join(UNIT_PATTERNS), flags=re.IGNORECASE)


def normalize_component(raw: str) -> str:
    """
    Uproszczona normalizacja składnika.
    Na tym etapie:
    - usuwa nawiasy
    - usuwa dawki i jednostki
    - czyści przecinki/spacje
    - zostawia nazwę substancji
    """
    value = raw.strip()
    value = PAREN_RE.sub(" ", value)
    value = UNIT_RE.sub(" ", value)
    value = value.replace(",", " ")
    value = value.replace(";", " ")
    value = MULTISPACE_RE.sub(" ", value).strip()

    return value


def split_substances(raw: str) -> List[str]:
    if not raw:
        return []

    parts = [p.strip() for p in raw.split("+")]
    parts = [p for p in parts if p]

    normalized = []
    for part in parts:
        clean = normalize_component(part)
        if clean:
            normalized.append(clean)

    return normalized


def main() -> None:
    with engine.begin() as conn:
        print("Czyszczenie poprzednich relacji...")
        conn.execute(text("DELETE FROM product_substances"))
        conn.execute(text("DELETE FROM substances"))

        print("Pobieranie produktów...")
        products = conn.execute(
            text("""
                SELECT id, active_substance_raw
                FROM medicinal_products
                WHERE active_substance_raw IS NOT NULL
                  AND TRIM(active_substance_raw) <> ''
                ORDER BY id
            """)
        ).mappings().all()

        print(f"Znaleziono produktów do analizy: {len(products)}")

        substances_cache: dict[str, int] = {}

        for product in products:
            product_id = product["id"]
            raw = product["active_substance_raw"]
            items = split_substances(raw)

            for idx, item in enumerate(items, start=1):
                substance_id = substances_cache.get(item)

                if substance_id is None:
                    inserted = conn.execute(
                        text("""
                            INSERT INTO substances(name)
                            VALUES (:name)
                            RETURNING id
                        """),
                        {"name": item},
                    ).mappings().first()

                    substance_id = inserted["id"]
                    substances_cache[item] = substance_id

                conn.execute(
                    text("""
                        INSERT INTO product_substances(
                            product_id,
                            substance_id,
                            raw_component,
                            component_order
                        )
                        VALUES (
                            :product_id,
                            :substance_id,
                            :raw_component,
                            :component_order
                        )
                    """),
                    {
                        "product_id": product_id,
                        "substance_id": substance_id,
                        "raw_component": item,
                        "component_order": idx,
                    },
                )

        total_substances = conn.execute(
            text("SELECT COUNT(*) AS cnt FROM substances")
        ).mappings().first()["cnt"]

        total_links = conn.execute(
            text("SELECT COUNT(*) AS cnt FROM product_substances")
        ).mappings().first()["cnt"]

        print(f"Zapisano substancji: {total_substances}")
        print(f"Zapisano relacji produkt-substancja: {total_links}")


if __name__ == "__main__":
    main()