import pandas as pd
from pathlib import Path
def read_excel_file(filename):
    current_dir = Path(__file__).parent

    file_path = current_dir / "datasets" / filename

    if file_path.exists():
        df = pd.read_excel(file_path)
        return df
    else:
        return f"File not found at: {file_path}"
    
