from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://drugs_user:drugs_pass@127.0.0.1:55432/drugs"

engine = create_engine(DATABASE_URL)


def detect_form_type(raw: str) -> str:
    if not raw:
        return "other"

    raw = raw.lower()

    if "tablet" in raw:
        return "tablet"

    if "kaps" in raw:
        return "capsule"

    if "syrop" in raw or "zawies" in raw or "roztw" in raw:
        return "liquid"

    if "granulat" in raw or "proszek" in raw:
        return "powder"

    return "other"


def main() -> None:
    with engine.begin() as conn:
        products = conn.execute(text("""
            SELECT id, pharmaceutical_form_raw
            FROM medicinal_products
        """)).mappings().all()

        form_types = {
            row["name"]: row["id"]
            for row in conn.execute(
                text("SELECT id, name FROM form_types")
            ).mappings().all()
        }

        updated = 0

        for product in products:
            detected = detect_form_type(product["pharmaceutical_form_raw"])
            form_type_id = form_types[detected]

            conn.execute(
                text("""
                    UPDATE medicinal_products
                    SET form_type_id = :form_type_id
                    WHERE id = :id
                """),
                {
                    "form_type_id": form_type_id,
                    "id": product["id"],
                }
            )

            updated += 1

    print(f"Updated {updated} products")


if __name__ == "__main__":
    main()