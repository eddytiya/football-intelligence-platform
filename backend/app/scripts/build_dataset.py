from pathlib import Path

from app.services.feature_engineering.dataset_builder import DatasetBuilder


def main():
    builder = DatasetBuilder()

    try:
        print("=" * 60)
        print("BUILDING FOOTBALL DATASET")
        print("=" * 60)

        dataset = builder.build_dataset()

        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "football_dataset.csv"

        dataset.to_csv(output_file, index=False)

        print("\nDataset successfully generated.\n")

        print(f"Saved to: {output_file}")

        print(f"Rows: {len(dataset)}")
        print(f"Columns: {len(dataset.columns)}")

        print(f"Missing values: {dataset.isnull().sum().sum()}")

        print(f"Duplicate rows: {dataset.duplicated().sum()}")

        print("\nFirst 10 columns:")
        for column in dataset.columns[:10]:
            print(f" - {column}")

    finally:
        builder.close()


if __name__ == "__main__":
    main()