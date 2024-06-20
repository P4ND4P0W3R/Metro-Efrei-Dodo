import datetime
import heapq
from db_config.models import Route, Trip, StopTime
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional

async def get_metro_graph(date: datetime.date):
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
        trips_for_route = await Trip.filter(route=route, service__start_date__lte=date.strftime("%Y%m%d"), service__end_date__gte=date.strftime("%Y%m%d")).prefetch_related("stop").all()
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

async def dijkstra(graph: Dict, start: str, end: str, date: datetime.date):
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

async def get_path_by_line(start_stop_id: str, end_stop_id: str, date: datetime.date):
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

async def get_path_with_transfers(start_stop_id: str, end_stop_id: str, date: datetime.date):
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