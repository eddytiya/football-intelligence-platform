from app.services.feature_engineering.dataset_builder import DatasetBuilder


def main():

    builder = DatasetBuilder()

    try:

        dataset = builder.build_dataset()

        print("\n========== DATASET ==========\n")

        print(dataset.head())

        print("\nRows:", len(dataset))
        print("Columns:", len(dataset.columns))

        print("\nColumn Names:\n")

        for column in dataset.columns:
            print(column)

    finally:

        builder.close()


if __name__ == "__main__":
    main()