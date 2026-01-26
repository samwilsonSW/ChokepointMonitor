from parseACLED import read_excel_file
from pathlib import Path
import re
import shutil

# Import the new importer
# from import_acled_xlsx import import_and_publish, import_and_publish_no_duplicate
from import_acled_xlsx import import_and_publish_no_duplicate


def main():
    base_dir = Path(__file__).resolve().parent.parent
    datasets_dir = base_dir / "datasets"


    # africaData = datasets_dir / "Africa_aggregated_data_up_to-2025-12-27.xlsx"
    # asiaData = datasets_dir / "Asia-Pacific_aggregated_data_up_to-2025-12-27.xlsx"
    # middleEastData = datasets_dir / "Middle-East_aggregated_data_up_to-2025-12-27.xlsx"

    # data_files = {
    #     "Africa": africaData,
    #     "Asia": asiaData,
    #     "Middle East": middleEastData,
    # }

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

def run_import(filename: str, min_year: int = 2023, table_name: str = 'ACLED-Aggregated-Conflict-Data'):
    """Wrapper to run the XLSX -> Supabase import for a given filename.

    - `filename`: path to the xlsx file to import.
    - `min_year`: only import rows where `week` year > min_year.
    - `table_name`: target Supabase table.
    """
    print(f"Running import for {filename} with min_year={min_year} into {table_name}...")
    import_and_publish_no_duplicate(filename, table_name=table_name, min_year=min_year)

    # After successful import, move the processed file from `datasets` to `datasets_old`
    try:
        src = Path(filename)
        if not src.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent
            src = base_dir / src
        dst_dir = src.parent.parent / "datasets_old"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        shutil.move(str(src), str(dst))
        print(f"Moved processed file to {dst}")
    except Exception as e:
        print(f"Warning: failed to move file {filename} to datasets_old: {e}")


if __name__ == "__main__":
    run_import("datasets/Asia-Pacific_aggregated_data_up_to-2026-01-10.xlsx", min_year=2023)