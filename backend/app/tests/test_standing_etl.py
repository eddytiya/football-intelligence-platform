from app.services.etl.standing_etl import StandingETL


def main():

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Standing ETL Test")
    print("=" * 70)

    try:

        print("\nInitializing ETL...")

        etl = StandingETL()

        print("✓ ETL initialized successfully.")

        print("\nRunning Standing ETL...\n")

        etl.run()

        print("\n✓ Standing ETL completed successfully.")

    except Exception as e:

        print("\n✗ Standing ETL failed.")

        print(e)

        raise


if __name__ == "__main__":
    main()

    