from pathlib import Path

SOURCE = Path(r"A:\drug-equivalents-app\data\Rejestr_Produktow_Leczniczych_calosciowy_stan_na_dzien_20260327 (1).csv")
TARGET = Path(r"A:\drug-equivalents-app\data\drugs_clean_utf8.csv")

def main() -> None:
    raw = SOURCE.read_bytes()

    text = raw.decode("cp1250", errors="replace")
    text = text.replace("\x00", "")

    TARGET.write_text(text, encoding="utf-8", newline="")

    print(f"Zapisano: {TARGET}")

if __name__ == "__main__":
    main()