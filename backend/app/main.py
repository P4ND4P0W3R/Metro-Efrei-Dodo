import json
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise
from tortoise.expressions import Q
from db_config.models import *
from db_config.config import TORTOISE_ORM, register_tortoise_orm
from typing import List, Dict, Optional, Any, re
from datetime import datetime, timedelta
import heapq
from services.graph import *
from services.connectivity import *
from services.mst import *
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5173",  # Your frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],  # Specify the HTTP methods your frontend uses
    allow_headers=["*"],  # Or specify specific headers if needed
)


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


# Register TortoiseORM with FastAPI
register_tortoise_orm(app, TORTOISE_ORM)


# -----------------------------------------------------------------------------
#                       DATABASE QUERIES
# -----------------------------------------------------------------------------

@app.get("/agencies")
async def get_agencies():
    agencies = await Agency.all()
    return [
        {
            "agency_id": agency.agency_id,
            "agency_name": agency.agency_name,
            "agency_url": agency.agency_url,
            "agency_timezone": agency.agency_timezone,
            "agency_lang": agency.agency_lang,
            "agency_phone": agency.agency_phone,
            "agency_email": agency.agency_email,
            "agency_fare_url": agency.agency_fare_url,
        }
        for agency in agencies
    ]


@app.get("/routes")
async def get_routes(agency_id: Optional[str] = Query(None)):
    if agency_id:
        routes = await Route.filter(agency__agency_id=agency_id).prefetch_related("agency").all()
    else:
        routes = await Route.all().prefetch_related("agency")
    return [
        {
            "route_id": route.route_id,
            "agency_id": route.agency.agency_id,
            "route_short_name": route.route_short_name,
            "route_long_name": route.route_long_name,
            "route_desc": route.route_desc,
            "route_type": route.route_type,
            "route_url": route.route_url,
            "route_color": route.route_color,
            "route_text_color": route.route_text_color,
            "route_sort_order": route.route_sort_order,
        }
        for route in routes
    ]


@app.get("/trips")
async def get_trips(route_id: Optional[str] = Query(None), service_id: Optional[str] = Query(None)):
    if route_id and service_id:
        trips = await Trip.filter(route__route_id=route_id, service__service_id=service_id).prefetch_related("route", "service").all()
    elif route_id:
        trips = await Trip.filter(route__route_id=route_id).prefetch_related("route", "service").all()
    elif service_id:
        trips = await Trip.filter(service__service_id=service_id).prefetch_related("route", "service").all()
    else:
        trips = await Trip.all().prefetch_related("route", "service")
    return [
        {
            "trip_id": trip.trip_id,
            "route_id": trip.route.route_id,
            "service_id": trip.service.service_id,
            "trip_headsign": trip.trip_headsign,
            "trip_short_name": trip.trip_short_name,
            "direction_id": trip.direction_id,
            "block_id": trip.block_id,
            "shape_id": trip.shape_id,
            "wheelchair_accessible": trip.wheelchair_accessible,
            "bikes_allowed": trip.bikes_allowed,
        }
        for trip in trips
    ]


@app.get("/stops")
async def get_stops(stop_id: Optional[str] = Query(None)):
    if stop_id:
        stops = await Stop.filter(stop_id=stop_id).all()
    else:
        stops = await Stop.all()
    return [
        {
            "stop_id": stop.stop_id,
            "stop_code": stop.stop_code,
            "stop_name": stop.stop_name,
            "stop_desc": stop.stop_desc,
            "stop_lon": stop.stop_lon,
            "stop_lat": stop.stop_lat,
            "zone_id": stop.zone_id,
            "stop_url": stop.stop_url,
            "location_type": stop.location_type,
            "parent_station": stop.parent_station,
            "stop_timezone": stop.stop_timezone,
            "level_id": stop.level_id,
            "wheelchair_boarding": stop.wheelchair_boarding,
            "platform_code": stop.platform_code,
        }
        for stop in stops
    ]


@app.get("/stations")
async def get_stations():
    """
    Calculates the barycenters of stations and returns associated route IDs.
    """
    stops = await Stop.all().prefetch_related("route_stops__route")

    # Group stops by parent_station
    grouped_stops = {}
    for stop in stops:
        parent_station = stop.parent_station
        if parent_station not in grouped_stops:
            grouped_stops[parent_station] = []
        grouped_stops[parent_station].append(stop)

    stations = []
    for parent_station, stop_group in grouped_stops.items():
        if not parent_station:
            continue

        total_lon = sum(stop.stop_lon for stop in stop_group)
        total_lat = sum(stop.stop_lat for stop in stop_group)
        count = len(stop_group)
        barycenter_lon = total_lon / count
        barycenter_lat = total_lat / count

        # Efficiently get distinct route IDs using prefetch_related data
        route_ids = set(route_stop.route.route_id for stop in stop_group for route_stop in stop.route_stops)

        # Read stations.json and get route_ids_with_sequences
        with open("./utils/stations.json", "r") as f:
            stations_data = json.load(f)
            for station_data in stations_data:
                if station_data["parent_station"] == parent_station:
                    route_ids_with_sequences = station_data["route_ids_with_sequences"]
                    break
            else:
                route_ids_with_sequences = []

        stations.append(
            {
                "parent_station": parent_station,
                "stop_name": stop_group[0].stop_name,
                "barycenter_lon": barycenter_lon,
                "barycenter_lat": barycenter_lat,
                "route_ids": list(route_ids),
                "stops": stop_group,
                "route_ids_with_sequences": route_ids_with_sequences
            }
        )

    return stations


@app.get("/stops/{stop_id}/metro_lines")
async def get_metro_lines_for_stop(stop_id: str):
    stop = await Stop.get(stop_id=stop_id).prefetch_related("route_stops", "route_stops__route")
    metro_lines = [
        {
            "route_id": route_stop.route.route_id,
            "route_short_name": route_stop.route.route_short_name
        }
        for route_stop in stop.route_stops if route_stop.route.route_type == 1  # Filter for metro lines
    ]
    return metro_lines


@app.get("/stop_times")
async def get_stop_times(trip_id: Optional[str] = Query(None)):
    if trip_id:
        stop_times = await StopTime.filter(trip__trip_id=trip_id).prefetch_related("trip", "stop").order_by(
            "stop_sequence").all()
    else:
        stop_times = await StopTime.all().prefetch_related("trip", "stop")
    return [
        {
            "trip_id": stop_time.trip.trip_id,
            "departure_time": stop_time.departure_time,
            "stop_id": stop_time.stop.stop_id,
            "stop_sequence": stop_time.stop_sequence,
            "stop_headsign": stop_time.stop_headsign
        }
        for stop_time in stop_times
    ]


@app.get("/transfers")
async def get_transfers(from_stop_id: Optional[str] = Query(None), to_stop_id: Optional[str] = Query(None)):
    if from_stop_id and to_stop_id:
        transfers = await Transfer.filter(from_stop__stop_id=from_stop_id,
                                          to_stop__stop_id=to_stop_id).prefetch_related("from_stop", "to_stop").all()
    elif from_stop_id:
        transfers = await Transfer.filter(from_stop__stop_id=from_stop_id).prefetch_related("from_stop",
                                                                                            "to_stop").all()
    elif to_stop_id:
        transfers = await Transfer.filter(to_stop__stop_id=to_stop_id).prefetch_related("from_stop", "to_stop").all()
    else:
        transfers = await Transfer.all().prefetch_related("from_stop", "to_stop")
    return [
        {
            "from_stop_id": transfer.from_stop.stop_id,
            "to_stop_id": transfer.to_stop.stop_id,
            "transfer_type": transfer.transfer_type,
            "min_transfer_time": transfer.min_transfer_time,
        }
        for transfer in transfers
    ]


@app.get("/pathways")
async def get_pathways(from_stop_id: Optional[str] = Query(None), to_stop_id: Optional[str] = Query(None)):
    if from_stop_id and to_stop_id:
        pathways = await Pathway.filter(from_stop__stop_id=from_stop_id, to_stop__stop_id=to_stop_id).prefetch_related(
            "from_stop", "to_stop").all()
    elif from_stop_id:
        pathways = await Pathway.filter(from_stop__stop_id=from_stop_id).prefetch_related("from_stop", "to_stop").all()
    elif to_stop_id:
        pathways = await Pathway.filter(to_stop__stop_id=to_stop_id).prefetch_related("from_stop", "to_stop").all()
    else:
        pathways = await Pathway.all().prefetch_related("from_stop", "to_stop")
    return [
        {
            "pathway_id": pathway.pathway_id,
            "from_stop_id": pathway.from_stop.stop_id,
            "to_stop_id": pathway.to_stop.stop_id,
            "pathway_mode": pathway.pathway_mode,
            "is_bidirectional": pathway.is_bidirectional,
            "length": pathway.length,
            "traversal_time": pathway.traversal_time,
            "stair_count": pathway.stair_count,
            "max_slope": pathway.max_slope,
            "min_width": pathway.min_width,
            "signposted_as": pathway.signposted_as,
            "reversed_signposted_as": pathway.reversed_signposted_as,
        }
        for pathway in pathways
    ]


@app.get("/stop_extensions")
async def get_stop_extensions(object_id: Optional[str] = Query(None)):
    if object_id:
        stop_extensions = await StopExtension.filter(object_id=object_id).all()
    else:
        stop_extensions = await StopExtension.all()
    return [
        {
            "object_id": stop_extension.object_id,
            "object_system": stop_extension.object_system,
            "object_code": stop_extension.object_code,
        }
        for stop_extension in stop_extensions
    ]


@app.get("/calendar")
async def get_calendar(service_id: Optional[str] = Query(None)):
    if service_id:
        calendar = await Calendar.filter(service_id=service_id).all()
    else:
        calendar = await Calendar.all()
    return [
        {
            "service_id": cal.service_id,
            "monday": cal.monday,
            "tuesday": cal.tuesday,
            "wednesday": cal.wednesday,
            "thursday": cal.thursday,
            "friday": cal.friday,
            "saturday": cal.saturday,
            "sunday": cal.sunday,
            "start_date": cal.start_date,
            "end_date": cal.end_date,
        }
        for cal in calendar
    ]


@app.get("/calendar_dates")
async def get_calendar_dates(service_id: Optional[str] = Query(None), date: Optional[str] = Query(None)):
    if service_id and date:
        calendar_dates = await CalendarDate.filter(service_id=service_id, date=date).all()
    elif service_id:
        calendar_dates = await CalendarDate.filter(service_id=service_id).all()
    elif date:
        calendar_dates = await CalendarDate.filter(date=date).all()
    else:
        calendar_dates = await CalendarDate.all()
    return [
        {
            "service_id": calendar_date.service_id,
            "date": calendar_date.date,
            "exception_type": calendar_date.exception_type,
        }
        for calendar_date in calendar_dates
    ]


@app.get("/stop_times/{trip_id}")
async def get_stop_times_for_trip(trip_id: str):
    """Get stop times for a specific trip ID.

    Args:
        trip_id: The trip ID to retrieve stop times for.

    Returns:
        A JSONResponse containing the stop times for the specified trip.
    """

    stop_times = await StopTime.filter(trip__trip_id=trip_id).prefetch_related("trip", "stop").order_by(
        "stop_sequence").all()

    return [
        {
            "trip_id": stop_time.trip.trip_id,
            "arrival_time": stop_time.arrival_time,
            "departure_time": stop_time.departure_time,
            "stop_id": stop_time.stop.stop_id,
            "stop_name": stop_time.stop.stop_name,  # Include stop name for better readability
            "stop_sequence": stop_time.stop_sequence,
            "pickup_type": stop_time.pickup_type,
            "drop_off_type": stop_time.drop_off_type,
            "local_zone_id": stop_time.local_zone_id,
            "stop_headsign": stop_time.stop_headsign,
            "timepoint": stop_time.timepoint,
        }
        for stop_time in stop_times
    ]


@app.get("/get_stop_times/{date_str}/{time_str}")
async def fetch_stop_times_and_trips(date_str: str, time_str: str):
    try:
        end_time_delta = int(time_str[0:2]) + 2
        end_time_str = str(end_time_delta) + time_str[2:]

        # Filtrer les StopTime après un certain horaire et les Trip disponibles à une date donnée
        stop_times = await StopTime.all().filter(
            (Q(arrival_time__gte=time_str) & Q(arrival_time__lte=end_time_str)) |
            (Q(departure_time__gte=time_str) & Q(departure_time__lte=end_time_str)),
            trip__service__start_date__lte=date_str,
            trip__service__end_date__gte=date_str
        ).prefetch_related('trip__route')

        return stop_times

    except ValueError:
        raise HTTPException(status_code=400,
                            detail="Invalid date or time format. Use YYYYMMDD for date and HH:MM:SS for time.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
#                       GRAPH ALGORITHMS
# -----------------------------------------------------------------------------


@app.get("/get_metro_graph/{date}/{time}")
async def get_metro_graph(date: str, time: str):
    """Constructs a weighted graph representing the metro network for a given date.

    Args:
        date: The date for which to construct the graph.
        time: The time for which to construct the graph.

    Returns:
        A dictionary representing the graph, with:
            - A dictionary containing the stations
            - A dictionary containing the trips
            - A dictionary containing the stops
            - A dictionary containing the routes
            - A dictionary containing the stop times for each stops
            - A dictionary containing the stop times for each trips
    """

    stop_times = await fetch_stop_times_and_trips(date, time)

    stops_times = {}
    trips_times = {}
    trips = {}
    routes = {}
    for stop_time in stop_times:
        if not stops_times.get(stop_time.stop_id):
            stops_times[stop_time.stop_id] = []
        stops_times[stop_time.stop_id].append(stop_time)

        if not trips_times.get(stop_time.trip_id):
            trips_times[stop_time.trip_id] = []

        trips_times[stop_time.trip_id].append(stop_time)

        trips[stop_time.trip_id] = stop_time.trip
        routes[stop_time.trip.route_id] = stop_time.trip.route
    stations = await get_stations()
    stop_stations = {}
    stations_stations = {}
    for station in stations:
        stations_stations[station["parent_station"]] = station
        for stop in station["stops"]:
            stop_stations[stop.stop_id] = station["parent_station"]

    system = {"stations": stations_stations, "trips": trips, "routes": routes, "stop_times": stops_times,
              "trips_times": trips_times, "stop_stations": stop_stations}
    return system


async def dijkstra(graph: Dict, start: str, end: str, date: datetime):
    """Computes the shortest path between two stations using Dijkstra's algorithm.

    Args:
        graph: The weighted graph representing the metro network.
        start: The starting station ID.
        end: The destination station ID.
        date: The date of the journey

    Returns:
        A dictionary containing:
            - Dictionary of the stations used
            - Dictionary of the stops used
            - Time used to travel the journey
    """

    start_station = graph['stations'].get(start)
    end_station = graph['stations'].get(end)

    if not (start_station and end_station):
        raise HTTPException(status_code=404, detail="Station not found")

    queue = [(None, start_station, None, {"stations": {start_station["parent_station"]: start_station}, "stops": {}, "final_date": date})]  # initialisation à la station de départ et à la date départ
    predecessors_stops = {}
    output = {}

    while queue:
        current_trip, current_station, current_stop, current_path = queue.pop(0)

        if current_station["parent_station"] == end_station["parent_station"]:  # condition "finale"
            print("reached : ", current_path["final_date"])
            if not output or output["final_date"] > current_path["final_date"]:
                print("updated : ", current_path)
                output = current_path

        # print(current_station["stops"])
        for stop in current_station["stops"]:  # On vérifie chacun des arrêts de la station
            # print("Checking ", stop.stop_id)

            if current_stop and stop.stop_id == current_stop.stop_id:  # cas sans changement de métro (donc pas de changement d'arrêt)

                next_time = next((st for st in graph["stop_times"].get(stop.stop_id) if st.trip == current_trip), None)  # recherche du stop time à cet arrêt du même métro
                if not next_time:
                    raise HTTPException(status_code=404, detail="Stop not found")  # Il devrait exister normalement...

                trip_times = graph["trips_times"].get(current_trip.trip_id)  # On recherche les arrêts du métro
                new_trip = current_trip  # On ne change pas de trip
                departure_date = get_date_from_stop_time_departure(next_time, date)  # On récupère l'heure de départ du train

            elif not current_stop or (stop.stop_id != current_stop.stop_id and stop.stop_id not in current_path["stops"]):  # cas avec changement de métro (et donc d'arrêt) ou de première itération sans aller à un arrêt déjà utilisé auparavant
                next_time = None
                departure_date = datetime.datetime(2500, 1, 1, 0, 0, 0)  # une date très éloignée pour faire référence lors d'une comparaisons

                times = graph["stop_times"].get(stop.stop_id)  # On récupère les heures de passages à cet arrêt
                if not times:  # cas ou il n'y en a pas -> pas possible d'aller plus loin par là
                    continue

                # On récupère l'heure de départ du premier passage de train après la date actuelle
                for stop_time2 in times:
                    temp_departure_date = get_date_from_stop_time_departure(stop_time2, date)
                    if departure_date and departure_date >= temp_departure_date > current_path["final_date"]:
                        next_time = stop_time2
                        departure_date = datetime.datetime.combine(temp_departure_date.date(), temp_departure_date.time())

                # Si on n'a pas pu en récupérer ou si l'arrêt a déjà été atteint avec un meilleur temps on passe au suivant
                if not next_time or (predecessors_stops.get(next_time.stop_id) and predecessors_stops[next_time.stop_id] < departure_date):
                    continue

                predecessors_stops[next_time.stop] = get_date_from_stop_time_arrival(next_time, date)  # On met à jour la meilleure date pour cet arrêt
                new_trip = graph["trips"].get(next_time.trip_id)  # On récupère le métro
                trip_times = graph["trips_times"].get(new_trip.trip_id)  # On récupère ses arrêts

            else:  # le reste
                print("No stop found")
                continue

            arrival_time = datetime.datetime(2500, 1, 1, 0, 0, 0)
            new_stop_time = None
            for stop_time in trip_times:  # On va récupérer le prochain arrêt du métro, il sera à la date la plus proche de la date de départ de l'arrêt actuel, c'est l'équivalent d'une fonction MIN
                new_arrival_date = get_date_from_stop_time_arrival(stop_time, date)
                if new_arrival_date > departure_date:  # Il faut que cette date se situe après dans le temps
                    if ((predecessors_stops.get(stop_time.stop) and predecessors_stops.get(stop_time.stop) > new_arrival_date)
                            or not predecessors_stops.get(stop_time.stop)):  # Il faut que cette date soit meilleure que celle enregistré pour ce nouvel arrêt, s'il y en a déjà une
                        if new_arrival_date < arrival_time:  # On récupère cette date si elle est plus proche que toutes celles parcourues jusque là
                            arrival_time = new_arrival_date
                            new_stop_time = stop_time

            # if not new_stop_time:  # cela veut dire que nous sommes déjà à un terminus pour ce train, il n'y a pas d'intérêt à continuer
                # print("no other stop from stop")

            if new_stop_time:

                # print("New stop from stop : ", new_stop_time.stop_id)

                if current_path["stops"].get(new_stop_time.stop_id):  # On vérifie si l'arrêt n'a pas déjà été parcouru dans ce voyage
                    # print("stop in path")
                    continue

                new_station = graph["stations"].get(graph["stop_stations"][new_stop_time.stop_id])  # On récupère la nouvelle station atteinte

                if not new_station or current_path["stations"].get(new_station["parent_station"]):  # On vérifie si elle n'a pas déjà été parcourue dans ce voyage
                    # print("station in path")
                    continue

                # On met à jour la meilleure date de passage pour cet arrêt (la nouvelle obtenue).
                predecessors_stops[new_stop_time.stop_id] = arrival_time

                # On récupère le chemin parcouru jusque là
                new_path = current_path.copy()

                # On ajoute la station au chemin
                new_path["stations"][new_station["parent_station"]] = new_station

                # On récupère le nouvel arrêt atteint
                new_stop = next((stop2 for stop2 in new_station["stops"] if stop2.stop_id == new_stop_time.stop_id), None)

                # On ajoute cet arrêt au chemin avec l'heure d'arrivée et de départ possible à cet arrêt
                new_path["stops"][new_stop.stop_id] = [new_stop_time.arrival_time, new_stop_time.departure_time]

                # On ajoute aussi l'arrêt précédent, utile si on a fait un changement de métro
                # La valeur restera la même pour l'arrêt si on n'a pas fait de changement de toutes façons (merci les dictionnaires)
                if not new_path["stops"].get(next_time.stop_id):
                    new_path["stops"][next_time.stop_id] = [next_time.arrival_time, next_time.departure_time]

                # enfin on met à jour la date actuelle à celle de notre arrivée dans la nouvelle station
                new_path["final_date"] = arrival_time

                # et voila... pourquoi ça marche pas ????
                queue.append((new_trip, new_station, new_stop, new_path))
                # print("added top path :\nStops : ", new_path["stops"])

    return output


def get_date_from_stop_time_departure(next_time, date):
    departure_time = next_time.departure_time
    hour = int(departure_time[0:2])
    minute = int(departure_time[3:5])
    second = int(departure_time[6:8])

    if hour > 23:
        hour -= 24
        date += timedelta(days=1)

    return datetime.datetime.combine(date.date(), datetime.time(hour, minute, second))


def get_date_from_stop_time_arrival(next_time, date):
    arrival_time = next_time.arrival_time
    hour = int(arrival_time[0:2])
    minute = int(arrival_time[3:5])
    second = int(arrival_time[6:8])

    if hour > 23:
        hour -= 24
        date += timedelta(days=1)

    return datetime.datetime.combine(date.date(), datetime.time(hour, minute, second))


async def get_path_by_line(start_stop_id: str, end_stop_id: str, date: datetime.datetime):
    """Get a path between two stops using a specific metro line

    Args:
        start_stop_id: ID of the starting station
        end_stop_id: ID of the destination station
        date: The date for the trip

    Returns:
        A dictionary containing:
            - shortest_path: The list of station IDs forming the path
            - total_time: The total travel time for the path.
    """

    # 1. Find all trips that pass both stops
    matching_trips = []
    stop_times = await StopTime.filter(stop__stop_id__in=[start_stop_id, end_stop_id]).order_by("stop_sequence").all()

    # 2. Create a dict with trip_id as key and a list of stops as value
    trip_stop_dict = {}
    for stop_time in stop_times:
        trip_id = stop_time.trip.trip_id
        if trip_id not in trip_stop_dict:
            trip_stop_dict[trip_id] = []
        trip_stop_dict[trip_id].append(stop_time.stop.stop_id)

    # 3. Check which trip contains both stations
    for trip_id, stops_for_trip in trip_stop_dict.items():
        if start_stop_id in stops_for_trip and end_stop_id in stops_for_trip:
            matching_trips.append(trip_id)

    # 4. Get all stop times for the matching trips
    path_stop_times = []
    for trip_id in matching_trips:
        stop_times_for_trip = await StopTime.filter(trip__trip_id=trip_id).order_by("stop_sequence").all()
        path_stop_times.extend(stop_times_for_trip)

    # 5. Build the path based on stop_times
    path = []
    for stop_time in path_stop_times:
        if stop_time.stop.stop_id == start_stop_id:
            path = [start_stop_id]
            break

    path_found = False
    for stop_time in path_stop_times:
        if stop_time.stop.stop_id == end_stop_id:
            path_found = True
            break
        if stop_time.stop.stop_id in path:
            continue
        path.append(stop_time.stop.stop_id)

    if not path_found:
        return {"shortest_path": [], "total_time": 0}

    # 6. Calculate total time
    total_time = 0
    for i in range(len(path) - 1):
        current_stop_id = path[i]
        next_stop_id = path[i + 1]

        # Calculate time difference
        time_format = "%H:%M:%S"
        arrival_time = datetime.datetime.strptime(path_stop_times[i + 1].arrival_time, time_format)
        departure_time = datetime.datetime.strptime(path_stop_times[i].departure_time, time_format)
        travel_time = (arrival_time - departure_time).total_seconds()
        total_time += travel_time

    return {"shortest_path": path, "total_time": total_time}


async def get_path_with_transfers(start_stop_id: str, end_stop_id: str, date: datetime):
    """Get a path between two stops considering transfers.

    Args:
        start_stop_id: ID of the starting station
        end_stop_id: ID of the destination station
        date: The date for the trip

    Returns:
        A dictionary
    """

    graph = await get_metro_graph(date.date().strftime("%Y%m%d"), date.time().strftime("%H%M%S"))
    result = await dijkstra(graph, start_stop_id, end_stop_id, date)
    return result


@app.get("/shortest_path/{start_stop_id}/{end_stop_id}/{date}")
async def get_shortest_path(start_stop_id: str, end_stop_id: str, date: str):
    """Finds the shortest path between two stops.

    Args:
        start_stop_id: The starting station ID.
        end_stop_id: The destination station ID.
        date: The date and time of the journey (YYYY-MM-DD HH:MM:SS)

    Returns:
        A JSONResponse containing the dictionary returned by the dijkstra algorithm.
    """

    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        result = await get_path_with_transfers(start_stop_id, end_stop_id, date_obj)
        return result
    except ValueError:
        return JSONResponse(content={"error": "Invalid date format. Please use YYYY-MM-DD HH:MM:SS."}, status_code=400)


# -----------------------------------------------------------------------------
#                       NETWORK CONNECTIVITY CHECK
# -----------------------------------------------------------------------------

async def check_network_connectivity(date: datetime.date):
    """Checks if the metro network is connected for a given date.

    Args:
        date: The date for which to check connectivity.

    Returns:
        True if the network is connected, False otherwise.
    """

    graph = await get_metro_graph(date)
    start_stop_id = list(graph.keys())[0]  # Choose any starting station
    visited = set()

    async def dfs(stop_id):
        visited.add(stop_id)
        for neighbor in graph[stop_id]:
            if neighbor not in visited:
                await dfs(neighbor)

    await dfs(start_stop_id)
    return len(visited) == len(graph)


@app.get("/connectivity")
async def check_connectivity(date: str):
    """Endpoint to check network connectivity.

    Args:
        date: The date to check (YYYY-MM-DD)

    Returns:
        A JSONResponse indicating whether the network is connected.
    """

    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        connected = await check_network_connectivity(date_obj)
        return JSONResponse(content={"connected": connected})
    except ValueError:
        return JSONResponse(content={"error": "Invalid date format. Please use YYYY-MM-DD."}, status_code=400)


# -----------------------------------------------------------------------------
#                       MINIMUM SPANNING TREE (Kruskal)
# -----------------------------------------------------------------------------

class DisjointSet:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, u):
        if self.parent[u] != u:
            self.parent[u] = self.find(self.parent[u])
        return self.parent[u]

    def union(self, u, v):
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u == root_v:
            return
        if self.rank[root_u] < self.rank[root_v]:
            self.parent[root_u] = root_v
        elif self.rank[root_u] > self.rank[root_v]:
            self.parent[root_v] = root_u
        else:
            self.parent[root_v] = root_u
            self.rank[root_u] += 1


async def kruskal(graph: Dict, date: datetime.date):
    """Computes the minimum spanning tree of the metro network using Kruskal's algorithm.

    Args:
        graph: The weighted graph representing the metro network.
        date: The date for which to compute the MST.

    Returns:
        A list of edges in the MST, sorted by weight (travel time).
    """

    edges = []
    for stop1 in graph:
        for stop2, weight in graph[stop1].items():
            edges.append((weight, stop1, stop2))
    edges.sort()

    num_stops = len(graph)
    disjoint_set = DisjointSet(num_stops)
    mst = []
    total_weight = 0

    for weight, stop1, stop2 in edges:
        if disjoint_set.find(stop1) != disjoint_set.find(stop2):
            disjoint_set.union(stop1, stop2)
            mst.append((stop1, stop2, weight))
            total_weight += weight

    return mst, total_weight


@app.get("/minimum_spanning_tree")
async def get_minimum_spanning_tree(date: str):
    """Endpoint to compute the minimum spanning tree.

    Args:
        date: The date to compute the MST for (YYYY-MM-DD)

    Returns:
        A JSONResponse containing the MST edges and its total weight.
    """

    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        graph = await get_metro_graph(date_obj)
        mst, total_weight = await kruskal(graph, date_obj)
        return JSONResponse(content={"mst": mst, "total_weight": total_weight})
    except ValueError:
        return JSONResponse(content={"error": "Invalid date format. Please use YYYY-MM-DD."}, status_code=400)


# -----------------------------------------------------------------------------
#                       RUN THE APP
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
