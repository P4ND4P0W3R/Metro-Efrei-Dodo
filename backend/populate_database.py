import time
import pandas as pd
from tortoise import Tortoise
from app.db_config.models import *
from app.db_config.config import DATABASE_URL
import asyncio

BATCH_SIZE = 1500

async def bulk_insert(model, data):
    await model.bulk_create(data)

async def populate_model(model, file_path, key_field=None):
    df = pd.read_csv(file_path)
    total_rows = len(df)
    chunk_size = max(total_rows // 200, 1)
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
                        row[key] = 0 
                    elif key == 'stop_timezone':
                        row[key] = 'Europe/Paris'
                    else:
                        row[key] = None

            batch.append(model(**row))

            if len(batch) >= BATCH_SIZE:
                await bulk_insert(model, batch)
                batch.clear()

        if batch:
            await bulk_insert(model, batch)

    tasks = [process_chunk(chunk) for chunk in chunks]
    await asyncio.gather(*tasks)
    print(f"{model.__name__} populated.")

async def populate_route_stop():
    """Populates the RouteStop junction table."""
    stop_times = await StopTime.all().prefetch_related("trip", "stop", "trip__route")
    route_stop_data = []
    for stop_time in stop_times:
        route = stop_time.trip.route
        stop = stop_time.stop

        # Avoid duplicates using 'exists()'
        if not await RouteStop.filter(route=route, stop=stop).exists():
            route_stop_data.append(RouteStop(route=route, stop=stop))

        if len(route_stop_data) >= BATCH_SIZE:
            await bulk_insert(RouteStop, route_stop_data)
            route_stop_data.clear()

    if route_stop_data:
        await bulk_insert(RouteStop, route_stop_data)
    print("RouteStop table populated.")

async def populate_trip_stop():
    """Populates the TripStop junction table."""
    stop_times = await StopTime.all().prefetch_related("trip", "stop")
    trip_stop_data = []
    for stop_time in stop_times:
        trip = stop_time.trip
        stop = stop_time.stop

        # Avoid duplicates using 'exists()'
        if not await TripStop.filter(trip=trip, stop=stop).exists():
            trip_stop_data.append(TripStop(trip=trip, stop=stop, stop_sequence=stop_time.stop_sequence)) 

        if len(trip_stop_data) >= BATCH_SIZE:
            await bulk_insert(TripStop, trip_stop_data)
            trip_stop_data.clear()

    if trip_stop_data:
        await bulk_insert(TripStop, trip_stop_data)
    print("TripStop table populated.")

async def main():
    start_time = time.time() 

    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.db_config.models"]},
    )
    await Tortoise.generate_schemas()

    await populate_model(Agency, "./data/clean2_gtfs/agency.txt", key_field='agency_id')
    await populate_model(Calendar, "./data/clean2_gtfs/calendar.txt", key_field='service_id')
    await populate_model(CalendarDate, "./data/clean2_gtfs/calendar_dates.txt")
    await populate_model(Route, "./data/clean2_gtfs/routes.txt", key_field='route_id')
    await populate_model(Stop, "./data/clean2_gtfs/stops.txt", key_field='stop_id')
    await populate_model(Trip, "./data/clean2_gtfs/trips.txt", key_field='trip_id')
    await populate_model(StopTime, "./data/clean2_gtfs/stop_times.txt")
    await populate_model(Transfer, "./data/clean2_gtfs/transfers.txt")
    await populate_model(Pathway, "./data/clean2_gtfs/pathways.txt", key_field='pathway_id')
    await populate_model(StopExtension, "./data/clean2_gtfs/stop_extensions.txt")

    await populate_route_stop()  # Populate the RouteStop table
    await populate_trip_stop()   # Populate the TripStop table

    await Tortoise.close_connections()

    end_time = time.time()  
    total_time = end_time - start_time  
    print(f"Total execution time: {total_time} seconds")

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())