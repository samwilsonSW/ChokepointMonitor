from parseACLED import read_excel_file


def main():
  africaData = "/Users/duk/Desktop/Chokepoint Monitor/datasets/Africa_aggregated_data_up_to-2025-12-27.xlsx"
  asiaData = "/Users/duk/Desktop/Chokepoint Monitor/datasets/Asia_aggregated_data_up_to-2025-12-27.xlsx"
  middleEastData = "/Users/duk/Desktop/Chokepoint Monitor/datasets/Middle_East_aggregated_data_up_to-2025-12-27.xlsx"

  data_files = {
    "Africa": africaData,
    "Asia": asiaData,
    "Middle East": middleEastData,
  }

  for name, path in data_files.items():
    print(f"Reading {name} from {path}...")
    try:
      result = read_excel_file(path)
      print(f"Result for {name}: {result}")
    except Exception as e:
      print(f"Error reading {name}: {e}")


if __name__ == "__main__":
  main()