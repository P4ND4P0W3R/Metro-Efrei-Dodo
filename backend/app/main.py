import json
import time

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
import copy

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
async def get_routes(agency_id: Optional[str] = None) -> List[dict]:
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
    begin_time = time.time()
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

    print("fetch time at stations", time.time() - begin_time)
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
        } for transfer in transfers
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


@app.get("/get_stop_times/{date_str}/{time_str}")
async def fetch_stop_times_and_trips(date_str: str, time_str: str) -> List[Dict[str, Any]]:
    try:
        end_time_delta = int(time_str[0:2]) + 3
        end_time_str = str(end_time_delta) + time_str[2:]

        # Filtrer les StopTime après un certain horaire et les Trip disponibles à une date donnée
        stop_times = await StopTime.filter(
            (Q(arrival_time__gte=time_str) & Q(arrival_time__lte=end_time_str)) |
            (Q(departure_time__gte=time_str) & Q(departure_time__lte=end_time_str)),
            trip__service__start_date__lte=date_str,
            trip__service__end_date__gte=date_str
        ).prefetch_related('trip__route').all()

        # Structurer les résultats
        results = []
        for stop_time in stop_times:
            results.append({
                "trip_id": stop_time.trip.trip_id,
                "route_short_name": stop_time.trip.route.route_short_name,
                "arrival_time": stop_time.arrival_time,
                "departure_time": stop_time.departure_time
            })

        return results

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format. Use YYYYMMDD for date and HH:MM:SS for time.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        begin_time = time.time()
        end_time_delta = int(time_str[0:2]) + 3
        end_time_str = str(end_time_delta) + time_str[2:]
        print("init fetch")

        # Filtrer les StopTime après un certain horaire et les Trip et route disponibles à une date donnée
        stop_times = await StopTime.all().filter(
            (Q(arrival_time__gte=time_str) & Q(arrival_time__lte=end_time_str)) |
            (Q(departure_time__gte=time_str) & Q(departure_time__lte=end_time_str)),
            trip__service__start_date__lte=date_str,
            trip__service__end_date__gte=date_str
        ).prefetch_related('trip__route')

        print("fetch time at stop times: ", time.time() - begin_time)
        return stop_times

    except ValueError:
        raise HTTPException(status_code=400,
                            detail="Invalid date or time format. Use YYYYMMDD for date and HH:MM:SS for time.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
#                       GRAPH ALGORITHMS
# -----------------------------------------------------------------------------

class MetroSystem:
    def __init__(self):
        self.stations = {}


class Routes:
    def __init__(self, route_id: str, route_name: str):
        self.route_id = route_id
        self.route_name = route_name
        self.trips = {}


class Station:
    def __init__(self, station_id: str, station_name: str):
        self.station_id = station_id
        self.station_name = station_name
        self.routes = {}
        self.stops = []

    def __str__(self):
        return str({
            "name": self.station_name,
            "station_id": self.station_id
        })


class Stops:
    def __init__(self, stop_id: str, stop_name: str, station: Station):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.parent_station = station
        self.transfers = {}
        self.stop_times = []

    def __str__(self):
        return str({
            "stop_id": self.stop_id,
            "stop_name": self.stop_name,
        })


class Trips:
    def __init__(self, trip_id: str, route: Routes, direction: int):
        self.trip_id = trip_id
        self.direction_id = direction
        self.route = route
        self.head_stop = None
        self.stops = []


class StopTimes:
    def __init__(self, trip: Trips, stop: Stops, arrival_time: datetime.datetime, departure_time: datetime.datetime, stop_sequence: int):
        self.stop = stop
        self.trip = trip
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.stop_sequence = stop_sequence
        self.next_stop_time = None
        self.previous_stop_time = None

    def __str__(self):
        return str({
            "arrival time": self.arrival_time,
            "departure time": self.departure_time,
        })


async def get_metro_graph(date: str, time_date: str, date_obj: datetime.datetime):
    """Constructs a weighted graph representing the metro network for a given date.

    Args:
        :param time_date:
        :param date:
        :param date_obj:

    Returns:
        A MetroSystem object representing the graph during the allocated 3 or 2 hours

    """

    # création du graphe de base (stations, arrêts et transferts) :
    print("starting graph build.")
    start_time = time.time()

    system = MetroSystem()

    begin_time = time.time()
    route_fetch = await get_routes()
    print("fetch time at routes: ", time.time() - begin_time)
    stations_fetch = await get_stations()

    all_routes = {}
    all_stops = {}

    for station in stations_fetch:
        try:
            current_station = system.stations[station["parent_station"]]
            if current_station:
                continue
        except KeyError:
            current_station = Station(station["parent_station"], station["stop_name"])
            system.stations[current_station.station_id] = current_station

        for route in station["route_ids"]:
            try:
                current_route = all_routes[route]
            except KeyError:
                corresponding_route = None
                for route2 in route_fetch:
                    if route == route2["route_id"]:
                        corresponding_route = route2
                        break
                if not corresponding_route:
                    raise HTTPException(status_code=404, detail=f"Route id not found in fetched data : {route}")

                current_route = Routes(route, corresponding_route["route_long_name"])
                all_routes[route] = current_route

            current_station.routes[route] = current_route

        for stop in station["stops"]:
            current_stop = Stops(stop.stop_id, stop.stop_name, current_station)
            all_stops[current_stop.stop_id] = current_stop
            current_station.stops.append(current_stop)

    begin_time = time.time()
    transfers = await get_transfers()
    print("fetch time at transfers: ", time.time() - begin_time)

    for transfer in transfers:
        try:
            stop1 = all_stops[transfer["from_stop_id"]]
            stop2 = all_stops[transfer["to_stop_id"]]
        except KeyError:
            raise HTTPException(status_code=404, detail="Stop not found while adding transfers.")

        stop1.transfers[stop2] = transfer["min_transfer_time"]
        stop2.transfers[stop1] = transfer["min_transfer_time"]

    # création des métros et de leurs horaires de passages

    stop_times = await fetch_stop_times_and_trips(date, time_date)

    all_trips = {}

    for stop_time in stop_times:

        try:
            current_route = all_routes[stop_time.trip.route_id]
        except KeyError:
            raise HTTPException(status_code=404, detail=f"route not found at creation of trip and stop_time : {stop_time.trip.route_id}\n\n")

        try:
            current_trip = current_route.trips[stop_time.trip_id]
        except KeyError:
            current_trip = Trips(stop_time.trip_id, current_route, stop_time.trip.direction_id)
            current_route.trips[current_trip.trip_id] = current_trip
            all_trips[current_trip.trip_id] = current_trip

        current_stop = all_stops[stop_time.stop_id]
        current_stop_time = StopTimes(current_trip, current_stop, get_date_from_stop_time_arrival(stop_time, date_obj), get_date_from_stop_time_departure(stop_time, date_obj), stop_time.stop_sequence)
        current_stop.stop_times.append(current_stop_time)
        current_trip.stops.append(current_stop_time)

        if not current_trip.head_stop:
            current_trip.head_stop = stop_time.trip.trip_headsign

    for trip in all_trips.values():
        for stop_time in trip.stops:
            for stop_time2 in trip.stops:
                if not stop_time.next_stop_time and stop_time.departure_time < stop_time2.arrival_time:
                    stop_time.next_stop_time = stop_time2
                elif stop_time.departure_time < stop_time2.arrival_time < stop_time.next_stop_time.arrival_time:
                    stop_time.next_stop_time = stop_time2
                elif not stop_time.previous_stop_time and stop_time.arrival_time > stop_time2.departure_time:
                    stop_time.previous_stop_time = stop_time2
                elif stop_time.arrival_time > stop_time2.departure_time > stop_time.previous_stop_time.departure_time:
                    stop_time.previous_stop_time = stop_time2

    print("built graph")
    print("Total creation time: ", time.time() - start_time)
    return system


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


def dijkstra(graph: MetroSystem, start: str, end: str, date: datetime):
    """Computes the shortest path between two stations using Dijkstra's algorithm with a starting date.

    Args:
        graph: The weighted graph representing the metro network.
        start: The starting station ID.
        end: The destination station ID.
        date: The date of the journey

    Returns:
        A dictionary containing:
            - Dictionary of the stations used
            - Dictionary of the stops used
            - Time and the end of journey
    """
    start_time = time.time()

    start_station = graph.stations[start]
    end_station = graph.stations[end]

    if not (start_station and end_station):
        raise HTTPException(status_code=404, detail="Station not found")

    queue = [(None, start_station, None, [[start_station], {}, date])]  # initialisation à la station de départ et à la date départ
    predecessors_stops = {}
    output = {}

    while queue:
        current_trip, current_station, current_stop, current_path = queue.pop(0)

        if output and output[2] < current_path[2]:  # On vérifie si on a déjà une date d'arrivée potentielle et on la compare avec la date actuelle.
            continue

        if current_station == end_station:  # condition "finale"
            if not output or output[2] > current_path[2]:
                output = current_path
                continue

        for stop in current_station.stops:  # On vérifie chacun des arrêts de la station
            transfer_time = 2

            current_date = copy.deepcopy(current_path[2])
            if current_stop and stop != current_stop:  # On calcule l'heure à laquelle on arrive à l'arrêt si on effectue un changement
                if stop in current_path[1]:  # à condition qu'il ne soit pas déjà dans le chemin parcouru bien évidemment
                    continue

                try:
                    transfer_time = current_stop.transfers[stop]
                except KeyError:
                    pass
                current_date += timedelta(seconds=transfer_time)

                # On regarde si on n'est pas déjà parvenu plus tôt à cet arrêt dans un autre parcours
                try:
                    current_record = predecessors_stops[stop]
                except KeyError:
                    current_record = None

                if current_record and current_record < current_date:
                    continue
                elif current_record and current_record > current_date:
                    predecessors_stops[stop] = current_date
                if not current_record:
                    predecessors_stops[stop] = current_date

            directions = {}  # On regarde toutes les directions possibles des trains passant à cet arrêt après la date actuelle
            for stop_time in stop.stop_times:
                try:
                    current_first_train_for_direction = directions[stop_time.trip.head_stop]
                    if current_first_train_for_direction.departure_time > stop_time.departure_time > current_date:
                        directions[stop_time.trip.head_stop] = stop_time
                except KeyError:
                    if stop_time.departure_time > current_date:
                        directions[stop_time.trip.head_stop] = stop_time

            # On regarde l'arrêt suivant d'un train pour chaque direction, s'il y en a deux identiques, on ne retient qu'une seule des deux directions car cela veut dire que la séparation de la ligne n'a pas lieux à cet arrêt.
            to_delete = []
            for direction in directions:
                if direction in to_delete:
                    continue
                for direction2 in directions:
                    if direction != direction2 and directions[direction].next_stop_time == directions[direction2].next_stop_time:
                        to_delete.append(direction2)

            for key in to_delete:
                del directions[key]

            # On va créer un nouveau parcours pour chacune des directions disponibles
            for (direction, next_time) in directions.items():

                if not next_time.next_stop_time:  # On regarde si c'est un terminus
                    continue

                # On vérifie qu'on ne crée pas de cycle au prochain arrêt
                if next_time.next_stop_time.stop in current_path[1]:
                    continue

                # On compare avec le temps record enregistré pour le prochain arrêt
                try:
                    current_record = predecessors_stops[next_time.next_stop_time.stop]
                except KeyError:
                    current_record = None

                if current_record and current_record < next_time.next_stop_time.arrival_time:
                    continue
                elif current_record and current_record > next_time.next_stop_time.arrival_time:  # On met à jour la meilleure date pour le prochain arrêt si elle est meilleure
                    predecessors_stops[next_time.next_stop_time.stop] = next_time.next_stop_time.arrival_time
                elif not current_record:  # ceci indique que c'est la première fois qu'on atteint cet arrêt au cours de l'algorithme
                    predecessors_stops[next_time.next_stop_time.stop] = next_time.next_stop_time.arrival_time

                new_station = next_time.next_stop_time.stop.parent_station

                if current_path[0] and new_station in current_path[0]:
                    continue

                # On récupère le chemin parcouru jusque là et on ajoute les nouveaux éléments
                new_path_stations = current_path[0].copy()
                new_path_stations.append(new_station)
                new_path_stops = current_path[1].copy()
                new_path_time = next_time.next_stop_time.arrival_time

                # On ajoute aussi l'arrêt précédent si on a fait un changement de métro dans la station précédente
                try:
                    new_path_stops[next_time.stop]
                except KeyError:
                    new_path_stops[next_time.stop] = [next_time.arrival_time, next_time.departure_time]

                # On ajoute le nouvel arrêt au chemin avec l'heure d'arrivée et de départ actuellement disponible à cet arrêt
                new_path_stops[next_time.next_stop_time.stop] = [next_time.next_stop_time.arrival_time, next_time.next_stop_time.departure_time]

                queue.append((next_time.next_stop_time.trip, new_station, next_time.next_stop_time.stop, [new_path_stations, new_path_stops, new_path_time]))

    print("Dijkstra execution time : ", time.time() - start_time)
    if not output:
        return {}

    print("path found : \n")
    return {
        "stations": [
            {
                "name": station.station_name
            } for station in output[0]
        ],
        "stops": [
            {
                "station": stop.parent_station.station_id,
                "arrival_time": times[0],
                "departure_time": times[1]
            } for (stop, times) in output[1].items()
        ],
        "arrival_date": output[2]
    }


def dijkstra_revert(graph: MetroSystem, start: str, end: str, date: datetime):
    """Computes the shortest path between two stations using Dijkstra's algorithm with an ending date.

        Args:
            graph: The weighted graph representing the metro network.
            start: The starting station ID.
            end: The destination station ID.
            date: The date of the journey

        Returns:
            A dictionary containing:
                - Dictionary of the stations used
                - Dictionary of the stops used
                - Time and the end of journey
        """
    start_time = time.time()

    start_station = graph.stations[end]
    end_station = graph.stations[start]

    if not (start_station and end_station):
        raise HTTPException(status_code=404, detail="Station not found")

    queue = [(None, start_station, None,
              [[start_station], {}, date])]  # initialisation à la station de départ et à la date d'arrivée
    predecessors_stops = {}
    output = {}

    while queue:
        current_trip, current_station, current_stop, current_path = queue.pop(0)

        if output and output[2] > current_path[2]:  # On vérifie si on a déjà une date de départ potentielle et on la compare avec la date actuelle.
            continue

        if current_station == end_station:  # condition "finale"
            if not output or output[2] < current_path[2]:
                output = current_path
                continue
#
        for stop in current_station.stops:  # On vérifie chacun des arrêts de la station
            transfer_time = 2

            current_date = copy.deepcopy(current_path[2])
            if current_stop and stop != current_stop:  # On calcule l'heure à laquelle on arrive à l'arrêt si on effectue un changement
                if stop in current_path[1]:  # à condition qu'il ne soit pas déjà dans le chemin parcouru bien évidemment
                    continue

                try:
                    transfer_time = current_stop.transfers[stop]
                except KeyError:
                    pass
                current_date -= timedelta(seconds=transfer_time)

                # On regarde si on n'est pas déjà parvenu plus tard à cet arrêt dans un autre parcours
                try:
                    current_record = predecessors_stops[stop]
                except KeyError:
                    current_record = None

                if current_record and current_record > current_date:
                    continue
                elif current_record and current_record < current_date:
                    predecessors_stops[stop] = current_date
                if not current_record:
                    predecessors_stops[stop] = current_date

            directions = {}
            # On regarde toutes les directions possibles des trains passant à cet arrêt avant l'heure actuelle.
            for stop_time in stop.stop_times:
                try:
                    if stop_time.previous_stop_time:
                        current_last_train_from_direction = directions[stop_time.previous_stop_time.stop]
                        if current_last_train_from_direction.arrival_time < stop_time.arrival_time < current_date:
                            directions[stop_time.previous_stop_time.stop] = stop_time
                except KeyError:
                    if stop_time.arrival_time < current_date:
                        directions[stop_time.previous_stop_time.stop] = stop_time

            # Si l'arrêt est déjà dans le chemin alors on peut ignorer cette direction
            for stop2 in current_path[1]:
                try:
                    del directions[stop2]
                except KeyError:
                    pass

            # On va créer un nouveau parcours pour chacune des directions disponibles
            for (direction, previous_time) in directions.items():

                if not previous_time.previous_stop_time:  # On regarde si c'est un terminus (départ).
                    continue

                # On vérifie qu'on ne crée pas de cycle au prochain arrêt précédent
                if previous_time.previous_stop_time.stop in current_path[1]:
                    continue

                # On compare avec le temps record enregistré pour le précédent arrêt
                try:
                    current_record = predecessors_stops[previous_time.previous_stop_time.stop]
                except KeyError:
                    current_record = None

                if current_record and current_record > previous_time.previous_stop_time.arrival_time:
                    continue
                elif current_record and current_record < previous_time.previous_stop_time.arrival_time:  # On met à jour la meilleure date pour le prochain arrêt si elle est meilleure
                    predecessors_stops[previous_time.previous_stop_time.stop] = previous_time.previous_stop_time.arrival_time
                elif not current_record:
                    predecessors_stops[previous_time.previous_stop_time.stop] = previous_time.previous_stop_time.arrival_time

                new_station = previous_time.previous_stop_time.stop.parent_station

                if current_path[0] and new_station in current_path[0]:
                    continue

                # On récupère le chemin parcouru jusque là et on ajoute les nouveaux éléments
                new_path_stations = current_path[0].copy()
                new_path_stations.append(new_station)
                new_path_stops = current_path[1].copy()
                new_path_time = previous_time.previous_stop_time.departure_time

                # On ajoute aussi l'arrêt précédent si on a fait un changement de métro dans la station précédente
                try:
                    new_path_stops[previous_time.stop]
                except KeyError:
                    new_path_stops[previous_time.stop] = [previous_time.arrival_time, previous_time.departure_time]

                # On ajoute le nouvel arrêt au chemin avec l'heure d'arrivée et de départ actuellement disponible à cet arrêt
                new_path_stops[previous_time.previous_stop_time.stop] = [previous_time.previous_stop_time.arrival_time, previous_time.previous_stop_time.departure_time]

                queue.append((previous_time.previous_stop_time.trip, new_station, previous_time.previous_stop_time.stop, [new_path_stations, new_path_stops, new_path_time]))

    print("Revert dijkstra execution time : ", time.time() - start_time)
    if not output:
        return {}

    print("path found : \n")
    return {
            "stations": [
                {
                    "name": station.station_name
                } for station in output[0]
            ],
            "stops": [
                {
                    "station": stop.parent_station.station_id,
                    "arrival_time": times[0],
                    "departure_time": times[1]
                } for (stop, times) in output[1].items()
            ],
            "arrival_date": output[2]
        }


async def get_path_with_transfers(start_stop_id: str, end_stop_id: str, date: datetime, forward: bool):
    """Get a path between two stops considering transfers.

    Args:
        start_stop_id: ID of the starting station
        end_stop_id: ID of the destination station
        date: The date for the trip
        forward: True if the start date is provided, False if end date is provided instead

    Returns:
        A dictionary
    """
    graph = await get_metro_graph(date.date().strftime("%Y%m%d"), date.time().strftime("%H%M%S"), date)
    if not forward:
        date += timedelta(hours=3)
        result = dijkstra_revert(graph, start_stop_id, end_stop_id, date)
    else:
        result = dijkstra(graph, start_stop_id, end_stop_id, date)
    print(result)
    return result


@app.get("/shortest_path/{forward}/{start_stop_id}/{end_stop_id}/{date}")
async def get_shortest_path(forward: str, start_stop_id: str, end_stop_id: str, date: str):
    """Finds the shortest path between two stops.

    Args:
        start_stop_id: The starting station ID.
        end_stop_id: The destination station ID.
        date: The date and time of the journey (YYYY-MM-DD HH:MM:SS)
        forward: "True" if the start date is provided, "False" if end date is provided instead

    Returns:
        A JSONResponse containing the dictionary returned by the dijkstra algorithm.
    """

    try:
        print("here")
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        if forward == "True":
            forward = True
        else:
            forward = False

        if not forward:
            date_obj -= timedelta(hours=3)
        result = await get_path_with_transfers(start_stop_id, end_stop_id, date_obj, forward)

        return result
    except ValueError:
        return JSONResponse(content={"error": "Invalid date format. Please use YYYY-MM-DD HH:MM:SS."}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": e}, status_code=404)

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