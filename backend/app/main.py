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
    for stop_time in stop_times:
        if not stops_times.get(stop_time.stop_id):
            stops_times[stop_time.stop_id] = []
        stops_times[stop_time.stop_id].append(stop_time)

        if not trips_times.get(stop_time.trip_id):
            trips_times[stop_time.trip_id] = []
        trips_times[stop_time.trip_id].append(stop_time)

    trips = {}
    routes = {}
    for stop_time in stop_times:
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

    queue = [(None, start_station, None, {"stations": {}, "stops": {}, "final_date": date})]

    predecessors_stops = {}

    output = {}

    while queue:
        current_trip, current_station, current_stop, current_path = queue.pop(0)
        current_path["stations"][current_station["parent_station"]] = current_station

        if current_station == end_station:  # condition "finale"
            if not output or output["final_date"] > current_path["final_date"]:
                output = current_path

        for stop in current_station["stops"]:
            if stop == current_stop and stop.stop_name != current_stop["stop_name"]:
                next_time = next((st for st in graph["stop_times"].get(stop.stop_id) if st.trip == current_trip), None)
                if not next_time:
                    raise HTTPException(status_code=404, detail="Stop not found")

                trip_times = graph["trips"].get(current_trip["trip_id"])
                new_trip = current_trip

            elif not current_stop or stop != current_stop:
                next_time = None
                departure_date = None
                for stop_time in graph["stop_times"].get(stop.stop_id):
                    temp_departure_date = get_date_from_stop_time_departure(stop_time, date)
                    if not next_time or (departure_date and departure_date >= temp_departure_date >= current_path["final_date"]):
                        next_time = stop_time
                        departure_date = temp_departure_date

                if next_time.stop in current_path["stops"] or (predecessors_stops.get(next_time.stop) and predecessors_stops[next_time.stop] < departure_date):
                    continue

                predecessors_stops[next_time.stop] = next_time
                new_trip = graph["trips"].get(next_time.trip_id)
                trip_times = graph["trips"].get(new_trip.trip_id)

            else:
                continue

            for stop_time in trip_times:
                if ((new_trip.direction_id == '1' and int(stop_time["stop_sequence"]) - 1 == int(next_time.stop_sequence)) or
                    (new_trip.direction_id == '0' and int(next_time.stop_sequence) != 0 and int(stop_time["stop_sequence"]) + 1 == int(next_time.stop_sequence))) and \
                        (not predecessors_stops.get(stop_time["stop"]) or (predecessors_stops.get(stop_time["stop"]) > get_date_from_stop_time_departure(stop_time, date))):

                    if current_path["stops"].get(stop_time["stop"]):
                        continue

                    new_station = graph["stations"].get(graph["stop_stations"][stop_time["stop"]])
                    if not new_station or current_path["stations"].get(new_station["parent_station"]):
                        continue

                    current_path["stations"][new_station["parent_station"]] = new_station

                    new_stop = next((stop2 for stop2 in new_station["stops"] if stop2.stop_id == stop_time["stop"]), None)
                    current_path["stops"][new_stop["stop_id"]] = [stop_time["arrival_time"], stop_time["departure_time"]]

                    queue.append((new_trip, new_station, new_stop, current_path.copy()))

    final_date = output.get("final_date")
    if final_date:
        final_time = final_date - date
        print(final_date, final_time)

    return output


def get_date_from_stop_time_departure(next_time, date):
    departure_time = next_time.departure_time
    hour = int(departure_time[0:2])
    minute = int(departure_time[3:5])
    second = int(departure_time[6:8])

    if hour > 23:
        hour -= 24
        date += timedelta(days=1)

    return datetime.combine(date.date(), datetime.time(hour, minute, second))


def get_date_from_stop_time_arrival(next_time, date):
    arrival_time = next_time.arrival_time
    hour = int(arrival_time[0:2])
    minute = int(arrival_time[3:5])
    second = int(arrival_time[6:8])

    if hour > 23:
        hour -= 24
        date += timedelta(days=1)

    return datetime.combine(date.date(), datetime.time(hour, minute, second))


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


async def get_path_with_transfers(start_stop_id: str, end_stop_id: str, date: datetime.datetime):
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
        return JSONResponse(content=result)
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
