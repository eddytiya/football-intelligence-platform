from app.services.etl.stadium_etl import StadiumETL


def main():

    etl = StadiumETL()

    etl.run()


if __name__ == "__main__":
    main()