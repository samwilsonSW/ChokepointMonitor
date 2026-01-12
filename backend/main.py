from parseACLED import read_excel_file
from pathlib import Path
import re


def main():
    base_dir = Path(__file__).resolve().parent.parent
    datasets_dir = base_dir / "datasets"

    # Auto-discover files in the datasets directory and label them
    data_files = {}
    for p in sorted(datasets_dir.iterdir()):
        if not p.is_file():
            continue
        stem = p.stem
        label_key = re.split(r'[-_.]', stem)[0].strip()
        label = label_key.replace('_', ' ').title()
        if label in data_files:
            idx = 1
            new_label = f"{label} ({idx})"
            while new_label in data_files:
                idx += 1
                new_label = f"{label} ({idx})"
            label = new_label
        data_files[label] = p

    for name, path in data_files.items():
        print(f"Reading {name} from {path}...")
        try:
            result = read_excel_file(str(path))
            print(f"Result for {name}: {result}")
        except Exception as e:
            print(f"Error reading {name}: {e}")
    # test commit


if __name__ == "__main__":
    main()