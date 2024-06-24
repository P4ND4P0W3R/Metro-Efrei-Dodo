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
        trips = await Trip.filter(route__route_id=route_id, service__service_id=service_id).prefetch_related("route",
                                                                                                             "service").all()
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

        stations.append(
            {
                "parent_station": parent_station,
                "stop_name": stop_group[0].stop_name,
                "barycenter_lon": barycenter_lon,
                "barycenter_lat": barycenter_lat,
                "route_ids": list(route_ids),
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


@app.get("/get_stop_times/{date_str}/{time_str}/{end_or_start}")
async def fetch_stop_times_and_trips(date_str: str, time_str: str, end_or_start: str) -> List[Dict[str, Any]]:
    try:
        if end_or_start not in ["start", "end"]:
            raise HTTPException(status_code=400, detail="Invalide end or start format.")

        if end_or_start and end_or_start == "start":
            end_time_delta = int(time_str[0:2]) + 3
            end_time_str = str(end_time_delta) + time_str[2:]
        else:
            end_time_str = time_str
            end_time_delta = int(time_str[0:2]) - 3
            time_str = str(end_time_delta) + time_str[2:]

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


# -----------------------------------------------------------------------------
#                       GRAPH ALGORITHMS
# -----------------------------------------------------------------------------

async def get_metro_graph(date: datetime.datetime):
    """Constructs a weighted graph representing the metro network for a given date.

    Args:
        date: The date for which to construct the graph.

    Returns:
        A dictionary representing the graph, with:
            - keys: stop_id (station IDs)
            - values: a dictionary of neighboring stops and the corresponding travel time.
    """

    # 1. Get all metro routes
    metro_routes = await Route.filter(route_type=1)  # Route type 1 for Metro

    # 2. Get all trips for metro routes on the specified date
    trips = []
    for route in metro_routes:
        trips_for_route = await Trip.filter(route=route, service__start_date__lte=date.strftime("%Y%m%d"),
                                            service__end_date__gte=date.strftime("%Y%m%d")).prefetch_related(
            "stop").all()
        trips.extend(trips_for_route)

    # 3. Get all stop times for the trips
    stop_times = []
    for trip in trips:
        stop_times_for_trip = await StopTime.filter(trip=trip).order_by("stop_sequence").all()
        stop_times.extend(stop_times_for_trip)

    # 4. Create the graph
    graph = {}
    for i in range(len(stop_times) - 1):
        current_stop_id = stop_times[i].stop.stop_id
        next_stop_id = stop_times[i + 1].stop.stop_id

        # Check if stop_id is a 'StopPoint' to avoid adding connection to a 'StopArea'
        if "StopPoint" in stop_times[i].stop.stop_id:
            if current_stop_id not in graph:
                graph[current_stop_id] = {}
            # Calculate time difference
            time_format = "%H:%M:%S"
            arrival_time = datetime.datetime.strptime(stop_times[i + 1].arrival_time, time_format)
            departure_time = datetime.datetime.strptime(stop_times[i].departure_time, time_format)
            travel_time = (arrival_time - departure_time).total_seconds()
            graph[current_stop_id][next_stop_id] = travel_time
    return graph


async def dijkstra(graph: Dict, start: str, end: str, date: datetime.datetime):
    """Computes the shortest path between two stations using Dijkstra's algorithm.

    Args:
        graph: The weighted graph representing the metro network.
        start: The starting station ID.
        end: The destination station ID.
        date: The date of the journey

    Returns:
        A dictionary containing:
            - shortest_path: The list of stop_id's representing the shortest path.
            - total_time: The total travel time along the shortest path.
    """

    distances = {stop: float("inf") for stop in graph}
    distances[start] = 0

    # Priority queue (using heapq) to store (distance, stop) pairs
    queue = [(0, start)]

    predecessors = {}  # Track predecessors for path reconstruction

    while queue:
        current_distance, current_stop = heapq.heappop(queue)

        if current_stop == end:
            break

        for neighbor, travel_time in graph[current_stop].items():
            distance_to_neighbor = current_distance + travel_time
            if distance_to_neighbor < distances[neighbor]:
                distances[neighbor] = distance_to_neighbor
                predecessors[neighbor] = current_stop
                heapq.heappush(queue, (distance_to_neighbor, neighbor))

    shortest_path = []
    total_time = distances[end]
    current_stop = end

    while current_stop:
        shortest_path.append(current_stop)
        current_stop = predecessors.get(current_stop)

    shortest_path.reverse()
    return {"shortest_path": shortest_path, "total_time": total_time}


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
        A dictionary containing:
            - shortest_path: The list of station IDs forming the path
            - total_time: The total travel time for the path.
    """

    graph = await get_metro_graph(date)
    result = await dijkstra(graph, start_stop_id, end_stop_id, date)
    return result


@app.get("/shortest_path")
async def get_shortest_path(start_stop_id: str, end_stop_id: str, date: str):
    """Finds the shortest path between two stops.

    Args:
        start_stop_id: The starting station ID.
        end_stop_id: The destination station ID.
        date: The date of the journey (YYYY-MM-DD)

    Returns:
        A JSONResponse containing the shortest path and total travel time.
    """

    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        result = await get_path_with_transfers(start_stop_id, end_stop_id, date_obj)
        return JSONResponse(content=result)
    except ValueError:
        return JSONResponse(content={"error": "Invalid date format. Please use YYYY-MM-DD."}, status_code=400)


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
