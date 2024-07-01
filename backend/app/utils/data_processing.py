import pandas as pd
import os
import time

def clean_gtfs_data(gtfs_folder, cleaned_gtfs_folder):
    """Cleans GTFS data to include only RATP data and writes to a new folder.

    Args:
        gtfs_folder: The directory containing the GTFS files.
        cleaned_gtfs_folder: The directory to write the cleaned GTFS files.

    Returns:
        None
    """
    start_time = time.time()

    # Create the cleaned GTFS folder if it doesn't exist
    if not os.path.exists(cleaned_gtfs_folder):
        os.makedirs(cleaned_gtfs_folder)

    # Read agency.txt
    agency = pd.read_csv(f"{gtfs_folder}/agency.txt")

    # Filter agency.txt to include only RATP agencies
    ratp_agency = agency[agency["agency_id"] == "IDFM:Operator_100"]
    ratp_agency.to_csv(f"{cleaned_gtfs_folder}/agency.txt", index=False)

    # Read routes.txt
    routes = pd.read_csv(f"{gtfs_folder}/routes.txt")

    # Filter routes.txt to include only RATP routes
    ratp_routes = routes[routes["agency_id"] == "IDFM:Operator_100"]
    ratp_routes.to_csv(f"{cleaned_gtfs_folder}/routes.txt", index=False)

    # Filter routes.txt to keep only metro routes
    ratp_routes = ratp_routes[ratp_routes["route_type"] == 1]
    ratp_routes.to_csv(f"{cleaned_gtfs_folder}/routes.txt", index=False)

    # Filter trips.txt based on the remaining routes
    trips = pd.read_csv(f"{gtfs_folder}/trips.txt")
    trips = trips[trips["route_id"].isin(ratp_routes["route_id"])]
    trips.to_csv(f"{cleaned_gtfs_folder}/trips.txt", index=False)

    # Filter calendar.txt based on the remaining trips
    calendar = pd.read_csv(f"{gtfs_folder}/calendar.txt")
    calendar = calendar[calendar["service_id"].isin(trips["service_id"])]
    calendar.to_csv(f"{cleaned_gtfs_folder}/calendar.txt", index=False)

    # Filter calendar_dates.txt based on the remaining trips
    calendar_dates = pd.read_csv(f"{gtfs_folder}/calendar_dates.txt")
    calendar_dates = calendar_dates[calendar_dates["service_id"].isin(trips["service_id"])]
    calendar_dates.to_csv(f"{cleaned_gtfs_folder}/calendar_dates.txt", index=False)

    # Filter stop_times.txt based on the remaining trips
    stop_times = pd.read_csv(f"{gtfs_folder}/stop_times.txt")
    stop_times = stop_times[stop_times["trip_id"].isin(trips["trip_id"])]
    stop_times.to_csv(f"{cleaned_gtfs_folder}/stop_times.txt", index=False)

    # Filter stops.txt based on the remaining stop_times
    stops = pd.read_csv(f"{gtfs_folder}/stops.txt")
    stops = stops[stops["stop_id"].isin(stop_times["stop_id"])]
    stops.to_csv(f"{cleaned_gtfs_folder}/stops.txt", index=False)

    # Filter pathways.txt based on the remaining stops
    pathways = pd.read_csv(f"{gtfs_folder}/pathways.txt")
    pathways = pathways[pathways["from_stop_id"].isin(stops["stop_id"])]
    pathways = pathways[pathways["to_stop_id"].isin(stops["stop_id"])]
    pathways.to_csv(f"{cleaned_gtfs_folder}/pathways.txt", index=False)

    # Filter transfers.txt based on the remaining stops
    transfers = pd.read_csv(f"{gtfs_folder}/transfers.txt")
    transfers = transfers[transfers["from_stop_id"].isin(stops["stop_id"])]
    transfers = transfers[transfers["to_stop_id"].isin(stops["stop_id"])]
    transfers.to_csv(f"{cleaned_gtfs_folder}/transfers.txt", index=False)

    # Filter stop_extensions.txt based on the remaining stops
    stop_extensions = pd.read_csv(f"{gtfs_folder}/stop_extensions.txt")
    stop_extensions = stop_extensions[stop_extensions["object_id"].isin(stops["stop_id"])]
    stop_extensions.to_csv(f"{cleaned_gtfs_folder}/stop_extensions.txt", index=False)

    print(f"GTFS data cleaned successfully. Files written to: {cleaned_gtfs_folder}")

    end_time = time.time()  # Record the end time
    total_time = end_time - start_time  # Calculate the total execution time
    print(f"Total execution time: {total_time} seconds")

# Example usage
gtfs_folder = r"C:\Users\Paul\OneDrive - Efrei\Documents\EFREI\L3_2023-2024\S6\Mastercamp\Mastercamp-IT-2024\backend\data\raw_gtfs"
cleaned_gtfs_folder = r"C:\Users\Paul\OneDrive - Efrei\Documents\EFREI\L3_2023-2024\S6\Mastercamp\Mastercamp-IT-2024\backend\data\clean2_gtfs"
clean_gtfs_data(gtfs_folder, cleaned_gtfs_folder)