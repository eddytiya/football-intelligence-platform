from app.services.etl.team_etl import TeamETL

if __name__ == "__main__":
    etl = TeamETL()
    etl.run()