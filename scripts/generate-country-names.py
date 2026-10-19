import json
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r'^\s*([A-Z0-9]{3})\s*=', re.MULTILINE)
LOC_RE = re.compile(
    r'^\s*([A-Z0-9]{3}):\d+\s+"((?:[^"\\]|\\.)*)"',
    re.MULTILINE
)

def read_tags(root):
    tags = set()
    folder = root / "common" / "country_tags"

    if not folder.exists():
        print(f"UWAGA: brak katalogu tagów: {folder}")
        return tags

    for file in folder.rglob("*.txt"):
        try:
            content = file.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        tags.update(TAG_RE.findall(content))

    return tags

def read_localisation(root, names):
    folder = root / "localisation"

    if not folder.exists():
        print(f"UWAGA: brak katalogu lokalizacji: {folder}")
        return

    count = 0
    for file in folder.rglob("*.yml"):
        # Generator korzysta z angielskich plików lokalizacji.
        if "_l_english" not in file.name.lower():
            continue

        try:
            content = file.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue

        for tag, name in LOC_RE.findall(content):
            name = name.replace(r'\"', '"').strip()
            if name:
                names[tag] = name
                count += 1

    print(f"  {root.name}: odczytano {count} wpisów lokalizacji")

def main():
    if len(sys.argv) != 3:
        print('Użycie: python scripts/generate-country-names.py "ścieżka_do_gry" "ścieżka_do_moda"')
        return 1

    game = Path(sys.argv[1])
    mod = Path(sys.argv[2])

    for path in (game, mod):
        if not path.is_dir():
            print(f"BŁĄD: katalog nie istnieje: {path}")
            return 1

    print("Zbieram tagi państw...")
    tags = read_tags(game) | read_tags(mod)
    print(f"Znaleziono tagów w plikach country_tags: {len(tags)}")

    names = {}
    print("Czytam lokalizacje gry i moda...")
    read_localisation(game, names)
    read_localisation(mod, names)

    # Zostawiamy wyłącznie tagi faktycznie zdefiniowane jako państwa.
    result = {tag: names[tag] for tag in sorted(tags) if tag in names}

    output = Path("src") / "lib" / "country_names.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\nGotowe! Wygenerowano nazw dla {len(result)} tagów.")
    print(f"Plik: {output.resolve()}")

    missing = sorted(tags - names.keys())
    if missing:
        print(f"Tagi bez znalezionej nazwy: {len(missing)}")
        print(", ".join(missing[:30]))

    return 0

if __name__ == "__main__":
    sys.exit(main())
