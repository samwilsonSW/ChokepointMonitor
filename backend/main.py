from pathlib import Path
import re
import shutil

from import_acled_xlsx import import_and_publish
from geocode import get_location_data

def run_import(filename: str, min_year: int = 2023, table_name: str = 'ACLED-Aggregated-Conflict-Data'):
    """Wrapper to run the XLSX -> Supabase import for a given filename.

    - `filename`: path to the xlsx file to import.
    - `min_year`: only import rows where `week` year > min_year.
    - `table_name`: target Supabase table.
    """
    print(f"Running import for {filename} with min_year={min_year} into {table_name}...")
    import_and_publish(filename, table_name=table_name, min_year=min_year)

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

def geocode():
    get_location_data()


def run_all_imports_and_geocode():
    """Iterate all files in the `datasets` folder and call `run_import` on each.

    Uses the default `min_year` and `table_name` values from `run_import`.
    Continues processing remaining files if one fails.
    """
    base_dir = Path(__file__).resolve().parent.parent
    datasets_dir = base_dir / "datasets"
    if not datasets_dir.exists():
        print(f"Datasets directory not found: {datasets_dir}")
        return

    for p in sorted(datasets_dir.iterdir()):
        if not p.is_file():
            continue
        # skip hidden files
        if p.name.startswith('.') :
            continue
        try:
            print(f"Processing file: {p}")
            # pass the relative path so run_import's move logic resolves it
            rel = p.relative_to(base_dir)
            run_import(str(rel))
        except Exception as e:
            print(f"Error importing {p}: {e}")

    


if __name__ == "__main__":
    # run_all_imports_and_geocode()
    geocode()