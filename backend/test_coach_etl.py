from app.services.etl.coach_etl import CoachETL


def main():

    etl = CoachETL()

    etl.run()


if __name__ == "__main__":
    main()