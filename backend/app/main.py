import re
import unicodedata

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

app = FastAPI(title="Drug Equivalents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "postgresql+psycopg://drugs_user:drugs_pass@127.0.0.1:55432/drugs"
engine = create_engine(DATABASE_URL)

def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value

    replacements = {
        "Â¦": "¦",
        "Â°": "°",
        "â": "–",
        "â": "—",
        "â": "„",
        "â": "”",
        "â": "“",
        "â¢": "•",
        "Âµ": "µ",
        "Ã³": "ó",
        "Ã„": "Ą",
        "Ã„â¦": "ą",
        "Ã‡": "Ć",
        "Ã§": "ć",
        "Ã": "Ę",
        "Ãª": "ę",
        "Ã": "Ł",
        "Ã‚Â³": "ł",
        "Ã": "Ń",
        "Ã±": "ń",
        "Ã": "Ó",
        "Ãś": "ó",
        "Ã": "Ś",
        "Ãº": "ś",
        "Ã¹": "Ź",
        "Ãź": "ź",
        "ÃŻ": "Ż",
        "Ã¼": "ż",
    }

    for bad, good in replacements.items():
        cleaned = cleaned.replace(bad, good)

    return cleaned

def clean_product_dict(row: dict) -> dict:
    cleaned = dict(row)

    text_fields = [
        "brand_name",
        "common_name",
        "active_substance_raw",
        "strength_raw",
        "pharmaceutical_form_raw",
        "authorization_number",
        "atc_code",
        "ma_holder",
        "package_description",
        "leaflet_url",
        "characteristic_url",
    ]

    for field in text_fields:
        if field in cleaned:
            cleaned[field] = clean_text(cleaned.get(field))

    return cleaned


SUBSTANCE_ALIASES = {
    "sertralina": ["sertralinum"],
    "paracetamol": ["paracetamolum"],
    "ibuprofen": ["ibuprofenum"],
    "amoksycylina": ["amoxicillinum"],
    "klawulanian": ["acidum clavulanicum", "clavulanic acid"],
    "kwas klawulanowy": ["acidum clavulanicum", "clavulanic acid"],
    "metformina": ["metforminum"],
    "omeprazol": ["omeprazolum"],
    "pantoprazol": ["pantoprazolum"],
    "escitalopram": ["escitalopramum"],
    "citalopram": ["citalopramum"],
    "fluoksetyna": ["fluoxetinum"],
    "paroksetyna": ["paroxetinum"],
    "wenlafaksyna": ["venlafaxinum"],
    "mirtazapina": ["mirtazapinum"],
    "trazodon": ["trazodonum"],
    "bisoprolol": ["bisoprololum"],
    "ramipryl": ["ramiprilum"],
    "peryndopryl": ["perindoprilum"],
    "amlodypina": ["amlodipinum"],
    "atorwastatyna": ["atorvastatinum"],
    "rosuwastatyna": ["rosuvastatinum"],
    "simwastatyna": ["simvastatinum"],
    "lewotyroksyna": ["levothyroxinum", "levothyroxine sodium"],
    "loratadyna": ["loratadinum"],
    "cetyryzyna": ["cetirizinum"],
    "desloratadyna": ["desloratadinum"],
    "montelukast": ["montelukastum"],
    "drotaweryna": ["drotaverinum"],
    "diklofenak": ["diclofenacum"],
    "ketoprofen": ["ketoprofenum"],
    "naproksen": ["naproxenum"],
    "meloksykam": ["meloxicamum"],
    "nimesulid": ["nimesulidum"],
    "tramadol": ["tramadolum"],
    "kodeina": ["codeinum"],
    "morfina": ["morphinum"],
    "furosemid": ["furosemidum"],
    "spironolakton": ["spironolactonum"],
    "hydrochlorotiazyd": ["hydrochlorothiazidum"],
    "warfaryna": ["warfarinum"],
    "rywaroksaban": ["rivaroxabanum"],
    "apiksaban": ["apixabanum"],
    "dabigatran": ["dabigatranum"],
    "insulina": ["insulinum"],
    "salbutamol": ["salbutamolum"],
    "budezonid": ["budesonidum"],
    "amoksycylina z kwasem klawulanowym": ["amoxicillinum", "acidum clavulanicum"],
    "azitromycyna": ["azithromycinum"],
    "klarytromycyna": ["clarithromycinum"],
    "cefuroksym": ["cefuroximum"],
    "cefaleksyna": ["cefalexinum"],
    "ciprofloksacyna": ["ciprofloxacinum"],
    "lewofloksacyna": ["levofloxacinum"],
    "doksycyklina": ["doxycyclinum"],
    "metronidazol": ["metronidazolum"],
    "fluconazol": ["fluconazolum"],
    "acyklowir": ["aciclovirum"],
    "walsartan": ["valsartanum"],
    "losartan": ["losartanum"],
    "telmisartan": ["telmisartanum"],
    "pregabalina": ["pregabalinum"],
    "gabapentyna": ["gabapentinum"],
}


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value


def parse_brand_query(query: str) -> tuple[str, str | None]:
    q = query.strip()

    strength_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(mg|g|mcg|µg|ml)",
        q,
        flags=re.IGNORECASE,
    )

    strength_part = None
    brand_part = q

    if strength_match:
        strength_part = strength_match.group(0).strip()
        brand_part = q[:strength_match.start()].strip()

    if not brand_part:
        brand_part = q

    return brand_part, strength_part


def build_substance_variants(query: str) -> list[str]:
    raw = query.strip()
    norm = normalize_text(raw)

    variants: list[str] = []
    seen = set()

    def add(value: str):
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            variants.append(cleaned)

    add(raw)
    add(norm)

    for alias in SUBSTANCE_ALIASES.get(norm, []):
        add(alias)
        add(normalize_text(alias))

    if norm.endswith("ina"):
        add(norm[:-1] + "um")
    if norm.endswith("yna"):
        add(norm[:-1] + "um")
    if norm.endswith("ol"):
        add(norm + "um")

    return variants


@app.get("/")
def root():
    return {"message": "Drug Equivalents API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) AS cnt FROM medicinal_products"))
        row = result.mappings().first()
    return {"count": row["cnt"]}


@app.get("/search/brand")
def search_brand(q: str = Query(..., min_length=2)):
    brand_part, strength_part = parse_brand_query(q)

    if strength_part:
        sql = text("""
            SELECT
                id,
                source_product_id,
                brand_name,
                common_name,
                active_substance_raw,
                strength_raw,
                pharmaceutical_form_raw,
                form_type_id,
                CASE
                    WHEN LOWER(brand_name) = LOWER(:brand_exact)
                         AND LOWER(strength_raw) LIKE LOWER(:strength_like)
                    THEN 1
                    WHEN LOWER(brand_name) = LOWER(:brand_exact)
                    THEN 2
                    WHEN LOWER(brand_name) LIKE LOWER(:brand_starts)
                         AND LOWER(strength_raw) LIKE LOWER(:strength_like)
                    THEN 3
                    WHEN LOWER(brand_name) LIKE LOWER(:brand_starts)
                    THEN 4
                    WHEN LOWER(brand_name) LIKE LOWER(:brand_contains)
                         AND LOWER(strength_raw) LIKE LOWER(:strength_like)
                    THEN 5
                    ELSE 6
                END AS rank_score
            FROM medicinal_products
            WHERE
                LOWER(brand_name) = LOWER(:brand_exact)
                OR LOWER(brand_name) LIKE LOWER(:brand_starts)
                OR LOWER(brand_name) LIKE LOWER(:brand_contains)
            ORDER BY
                rank_score,
                brand_name,
                strength_raw
            LIMIT 20
        """)

        params = {
            "brand_exact": brand_part,
            "brand_starts": f"{brand_part}%",
            "brand_contains": f"%{brand_part}%",
            "strength_like": f"%{strength_part}%",
        }
    else:
        sql = text("""
            SELECT
                id,
                source_product_id,
                brand_name,
                common_name,
                active_substance_raw,
                strength_raw,
                pharmaceutical_form_raw,
                form_type_id,
                CASE
                    WHEN LOWER(brand_name) = LOWER(:brand_exact) THEN 1
                    WHEN LOWER(brand_name) LIKE LOWER(:brand_starts) THEN 2
                    WHEN LOWER(brand_name) LIKE LOWER(:brand_contains) THEN 3
                    ELSE 4
                END AS rank_score
            FROM medicinal_products
            WHERE
                LOWER(brand_name) = LOWER(:brand_exact)
                OR LOWER(brand_name) LIKE LOWER(:brand_starts)
                OR LOWER(brand_name) LIKE LOWER(:brand_contains)
            ORDER BY
                rank_score,
                brand_name,
                strength_raw
            LIMIT 20
        """)

        params = {
            "brand_exact": brand_part,
            "brand_starts": f"{brand_part}%",
            "brand_contains": f"%{brand_part}%",
        }

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return {
    "query": q,
    "parsed": {
        "brand_part": brand_part,
        "strength_part": strength_part,
    },
    "items": [clean_product_dict(dict(row)) for row in rows],
}


@app.get("/search/substance")
def search_substance(q: str = Query(..., min_length=2)):
    variants = build_substance_variants(q)

    if not variants:
        return {"query": q, "variants": [], "items": []}

    conditions = []
    params = {}

    for i, variant in enumerate(variants):
        param_name = f"v{i}"
        params[param_name] = f"%{variant}%"
        conditions.append(f"LOWER(mp.common_name) LIKE :{param_name}")
        conditions.append(f"LOWER(mp.active_substance_raw) LIKE :{param_name}")
        conditions.append(f"LOWER(s.name) LIKE :{param_name}")

    where_sql = " OR ".join(conditions)

    sql = text(f"""
        SELECT DISTINCT
            mp.id,
            mp.source_product_id,
            mp.brand_name,
            mp.common_name,
            mp.active_substance_raw,
            mp.strength_raw,
            mp.pharmaceutical_form_raw,
            mp.form_type_id
        FROM medicinal_products mp
        LEFT JOIN product_substances ps ON ps.product_id = mp.id
        LEFT JOIN substances s ON s.id = ps.substance_id
        WHERE {where_sql}
        ORDER BY mp.brand_name
        LIMIT 20
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return {
    "query": q,
    "variants": variants,
    "items": [clean_product_dict(dict(row)) for row in rows],
}


@app.get("/products/{product_id}")
def get_product(product_id: int):
    sql = text("""
        SELECT *
        FROM medicinal_products
        WHERE id = :id
    """)

    with engine.connect() as conn:
        row = conn.execute(sql, {"id": product_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    return dict(row)


@app.get("/products/{product_id}/substances")
def get_product_substances(product_id: int):
    with engine.connect() as conn:
        product = conn.execute(
            text("""
                SELECT id, brand_name, active_substance_raw
                FROM medicinal_products
                WHERE id = :id
            """),
            {"id": product_id},
        ).mappings().first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        rows = conn.execute(
            text("""
                SELECT
                    ps.component_order,
                    s.name AS substance_name,
                    ps.raw_component
                FROM product_substances ps
                JOIN substances s ON s.id = ps.substance_id
                WHERE ps.product_id = :id
                ORDER BY ps.component_order
            """),
            {"id": product_id},
        ).mappings().all()

    return {
        "product": dict(product),
        "substances": [dict(row) for row in rows],
    }


@app.get("/products/{product_id}/strengths")
def get_product_strengths(product_id: int):
    with engine.connect() as conn:
        product = conn.execute(
            text("""
                SELECT id, brand_name, strength_raw
                FROM medicinal_products
                WHERE id = :id
            """),
            {"id": product_id},
        ).mappings().first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        rows = conn.execute(
            text("""
                SELECT
                    id,
                    substance_id,
                    value,
                    unit
                FROM product_strengths
                WHERE product_id = :id
                ORDER BY id
            """),
            {"id": product_id},
        ).mappings().all()

    return {
        "product": dict(product),
        "strengths": [dict(row) for row in rows],
    }


@app.get("/products/{product_id}/equivalents")
def equivalents(product_id: int):
    with engine.connect() as conn:
        base = conn.execute(
            text("""
                SELECT
                    id,
                    brand_name,
                    common_name,
                    active_substance_raw,
                    strength_raw,
                    pharmaceutical_form_raw,
                    form_type_id
                FROM medicinal_products
                WHERE id = :id
            """),
            {"id": product_id},
        ).mappings().first()

        if not base:
            raise HTTPException(status_code=404, detail="Product not found")

        base_substances_rows = conn.execute(
            text("""
                SELECT s.id, s.name
                FROM product_substances ps
                JOIN substances s ON s.id = ps.substance_id
                WHERE ps.product_id = :id
                ORDER BY ps.component_order
            """),
            {"id": product_id},
        ).mappings().all()

        base_strength_rows = conn.execute(
            text("""
                SELECT substance_id, value, unit
                FROM product_strengths
                WHERE product_id = :id
                ORDER BY id
            """),
            {"id": product_id},
        ).mappings().all()

        if not base_substances_rows:
            return {
                "base": dict(base),
                "items": [],
                "meta": {"total": 0},
            }

        base_substance_names = [row["name"] for row in base_substances_rows]
        base_substance_ids = [row["id"] for row in base_substances_rows]
        base_substance_count = len(base_substance_names)

        base_strength_map = {
            row["substance_id"]: f'{row["value"]}:{row["unit"]}'
            for row in base_strength_rows
        }
        base_strength_signature = list(base_strength_map.values())
        base_strength_count = len(base_strength_signature)

        rows = conn.execute(
            text("""
                WITH candidate_matches AS (
                    SELECT
                        mp.id,
                        mp.brand_name,
                        mp.common_name,
                        mp.active_substance_raw,
                        mp.strength_raw,
                        mp.pharmaceutical_form_raw,
                        mp.form_type_id,
                        COUNT(DISTINCT s.id) AS matched_substances_count,
                        COUNT(DISTINCT ps_all.substance_id) AS total_substances_count
                    FROM medicinal_products mp
                    JOIN product_substances ps_match
                        ON ps_match.product_id = mp.id
                    JOIN substances s
                        ON s.id = ps_match.substance_id
                    JOIN product_substances ps_all
                        ON ps_all.product_id = mp.id
                    WHERE mp.id != :product_id
                      AND s.name = ANY(:substances)
                      AND mp.form_type_id = :base_form_type_id
                    GROUP BY
                        mp.id,
                        mp.brand_name,
                        mp.common_name,
                        mp.active_substance_raw,
                        mp.strength_raw,
                        mp.pharmaceutical_form_raw,
                        mp.form_type_id
                )
                SELECT
                    cm.id,
                    cm.brand_name,
                    cm.common_name,
                    cm.active_substance_raw,
                    cm.strength_raw,
                    cm.pharmaceutical_form_raw,
                    cm.form_type_id,
                    cm.matched_substances_count,
                    cm.total_substances_count,
                    (
                        SELECT COUNT(*)
                        FROM (
                            SELECT CONCAT(value, ':', unit) AS sig
                            FROM product_strengths
                            WHERE product_id = cm.id
                        ) s2
                        WHERE s2.sig = ANY(:base_strengths)
                    ) AS matched_strengths_count,
                    (
                        SELECT COUNT(*)
                        FROM product_strengths
                        WHERE product_id = cm.id
                    ) AS total_strengths_count
                FROM candidate_matches cm
                ORDER BY cm.brand_name
                LIMIT 200
            """),
            {
                "product_id": product_id,
                "substances": base_substance_names,
                "base_form_type_id": base["form_type_id"],
                "base_strengths": base_strength_signature,
            },
        ).mappings().all()

    items = []

    for row in rows:
        matched_substances_count = row["matched_substances_count"]
        total_substances_count = row["total_substances_count"]
        matched_strengths_count = row["matched_strengths_count"] or 0
        total_strengths_count = row["total_strengths_count"] or 0

        full_substances = (
            matched_substances_count == base_substance_count
            and total_substances_count == base_substance_count
        )

        full_strengths = (
            base_strength_count > 0
            and matched_strengths_count == base_strength_count
            and total_strengths_count == base_strength_count
        )

        same_form = row["form_type_id"] == base["form_type_id"]

        if full_substances and full_strengths and same_form:
            match_type = "identical"
            score = 100
        elif full_substances and same_form:
            match_type = "same_substances"
            score = 80
        elif matched_substances_count >= max(1, base_substance_count - 1):
            match_type = "partial_match"
            score = 50
        else:
            match_type = "weak_match"
            score = 10

        criteria = {
            "same_active_substances": full_substances,
            "same_strength_set": full_strengths,
            "same_form": same_form,
        }

        reason_tags = []
        if criteria["same_active_substances"]:
            reason_tags.append("Ta sama substancja czynna")
        if criteria["same_strength_set"]:
            reason_tags.append("Ta sama moc")
        if criteria["same_form"]:
            reason_tags.append("Ta sama postać")

        if not reason_tags and matched_substances_count > 0:
            reason_tags.append("Częściowe pokrycie składu")

        label = (
            "Idealny zamiennik" if score == 100 else
            "Ten sam skład, różnice w parametrach" if score == 80 else
            "Częściowe dopasowanie" if score == 50 else
            "Słabe dopasowanie"
        )

        items.append({
            "id": row["id"],
            "brand_name": row["brand_name"],
            "common_name": row["common_name"],
            "active_substance_raw": row["active_substance_raw"],
            "strength_raw": row["strength_raw"],
            "pharmaceutical_form_raw": row["pharmaceutical_form_raw"],
            "form_type_id": row["form_type_id"],
            "matched_substances_count": matched_substances_count,
            "total_substances_count": total_substances_count,
            "matched_strengths_count": matched_strengths_count,
            "total_strengths_count": total_strengths_count,
            "match_type": match_type,
            "score": score,
            "label": label,
            "criteria": criteria,
            "reason_tags": reason_tags,
        })

    items = [x for x in items if x["score"] >= 50]
    items.sort(key=lambda x: (-x["score"], -x["matched_substances_count"], x["brand_name"]))

    return {
        "base": {
            **dict(base),
            "normalized_substances": base_substance_names,
            "normalized_strengths": base_strength_signature,
        },
        "items": items[:50],
        "meta": {
            "total": len(items[:50]),
        }
    }


@app.get("/products/{product_id}/best-equivalents")
def best_equivalents(product_id: int):
    data = equivalents(product_id)

    best = [
        item for item in data["items"]
        if item["score"] >= 80 and item["match_type"] != "weak_match"
    ]

    return {
        "base": data["base"],
        "items": best[:10],
        "meta": {
            "total": len(best[:10])
        }
    }


@app.get("/products/{product_id}/pharmacy-equivalents")
def pharmacy_equivalents(product_id: int):
    data = equivalents(product_id)

    with engine.connect() as conn:
        base_details = conn.execute(
            text("""
                SELECT
                    id,
                    brand_name,
                    common_name,
                    active_substance_raw,
                    strength_raw,
                    pharmaceutical_form_raw,
                    authorization_number,
                    atc_code,
                    ma_holder,
                    package_description,
                    leaflet_url,
                    characteristic_url
                FROM medicinal_products
                WHERE id = :id
            """),
            {"id": product_id},
        ).mappings().first()

    if not base_details:
        raise HTTPException(status_code=404, detail="Product not found")

    identical = [clean_product_dict(i) for i in data["items"] if i["score"] == 100]
    same = [clean_product_dict(i) for i in data["items"] if i["score"] == 80]

    return {
        "base": clean_product_dict(dict(base_details)),
        "ideal": identical,
        "acceptable": same,
        "all_items": [clean_product_dict(i) for i in data["items"]],
        "meta": {
            "ideal_count": len(identical),
            "acceptable_count": len(same),
            "all_count": len(data["items"]),
        }
    }