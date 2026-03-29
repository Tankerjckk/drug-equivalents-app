import re
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://drugs_user:drugs_pass@127.0.0.1:55432/drugs"
engine = create_engine(DATABASE_URL)


def parse_strength(raw):
    if not raw:
        return []

    parts = raw.split("+")
    results = []

    for part in parts:
        part = part.strip()

        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(mg|g|ml)", part, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", "."))
            unit = match.group(2).lower()

            results.append({
                "value": value,
                "unit": unit
            })

    return results


def main():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM product_strengths"))

        products = conn.execute(text("""
            SELECT id, strength_raw
            FROM medicinal_products
            WHERE strength_raw IS NOT NULL
        """)).mappings().all()

        inserted = 0

        for p in products:
            parsed = parse_strength(p["strength_raw"])

            for item in parsed:
                conn.execute(text("""
                    INSERT INTO product_strengths (product_id, value, unit)
                    VALUES (:pid, :value, :unit)
                """), {
                    "pid": p["id"],
                    "value": item["value"],
                    "unit": item["unit"]
                })

                inserted += 1

        print(f"Inserted {inserted} strength rows")


if __name__ == "__main__":
    main()