import time
import pandas as pd
from tortoise import Tortoise
from backend.app.db_config.models import Agency, Route, Trip, Stop, StopTime, Transfer, Pathway, StopExtension, Calendar, CalendarDate
from backend.app.db_config.config import DATABASE_URL
import asyncio

BATCH_SIZE = 1500

async def bulk_insert(model, data):
    await model.bulk_create(data)

async def populate_model(model, file_path, key_field=None):
    df = pd.read_csv(file_path)  # Read the CSV file using pandas
    total_rows = len(df)
    chunk_size = max(total_rows // 200, 1)  # Ensure chunk size is at least 1
    chunks = [df[i:i + chunk_size] for i in range(0, total_rows, chunk_size)]

    async def process_chunk(chunk):
        batch = []
        for index, row in chunk.iterrows():
            if key_field and await model.filter(**{key_field: row[key_field]}).exists():
                continue

            # Convert empty strings to None for all fields
            for key, value in row.items():
                if pd.isna(value):
                    if key == 'zone_id':
                        row[key] = 0  # Provide a default value for zone_id
                    elif key == 'stop_timezone':
                        row[key] = 'Europe/Paris'  # Provide a default value for stop_timezone
                    else:
                        row[key] = None

            # Append the row to the batch
            batch.append(model(**row))

            if len(batch) >= BATCH_SIZE:
                await bulk_insert(model, batch)
                print("Batch inserted.")
                batch.clear()

        if batch:
            await bulk_insert(model, batch)

    tasks = [process_chunk(chunk) for chunk in chunks]
    await asyncio.gather(*tasks)
    print(f"{model.__name__} populated.")

async def main():
    start_time = time.time()  # Record the start time

    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["models"]},
    )
    await Tortoise.generate_schemas()

    await populate_model(Agency, "./data/clean_gtfs/agency.txt", key_field='agency_id')
    await populate_model(Calendar, "./data/clean_gtfs/calendar.txt", key_field='service_id')
    await populate_model(CalendarDate, "./data/clean_gtfs/calendar_dates.txt")
    await populate_model(Route, "./data/clean_gtfs/routes.txt", key_field='route_id')
    await populate_model(Stop, "./data/clean_gtfs/stops.txt", key_field='stop_id')
    await populate_model(Trip, "./data/clean_gtfs/trips.txt", key_field='trip_id')
    await populate_model(StopTime, "./data/clean_gtfs/stop_times.txt")
    await populate_model(Transfer, "./data/clean_gtfs/transfers.txt")
    await populate_model(Pathway, "./data/clean_gtfs/pathways.txt", key_field='pathway_id')
    await populate_model(StopExtension, "./data/clean_gtfs/stop_extensions.txt")

    await Tortoise.close_connections()

    end_time = time.time()  # Record the end time
    total_time = end_time - start_time  # Calculate the total execution time
    print(f"Total execution time: {total_time} seconds")

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
