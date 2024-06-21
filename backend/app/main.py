from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise
from db_config.models import Agency, Route, Trip, Stop, StopTime, Transfer, Pathway, StopExtension, Calendar, CalendarDate
from db_config.config import TORTOISE_ORM, register_tortoise_orm
from typing import List, Dict, Optional
import datetime
import heapq
from services.graph import *
from services.connectivity import *
from services.mst import *
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

@app.get("/barycenters")
async def get_barycenters():
    # Fetch all stops
    stops = await Stop.all()
    
    # Group stops by parent_station
    grouped_stops = {}
    for stop in stops:
        parent_station = stop.parent_station
        if parent_station not in grouped_stops:
            grouped_stops[parent_station] = []
        grouped_stops[parent_station].append(stop)
    
    # Calculate the barycenter for each parent station
    barycenters = []
    for parent_station, stop_group in grouped_stops.items():
        if not parent_station:  # Skip if there is no parent station
            continue
        total_lon = sum(stop.stop_lon for stop in stop_group)
        total_lat = sum(stop.stop_lat for stop in stop_group)
        stop_name = stop_group[0].stop_name
        count = len(stop_group)
        barycenter_lon = total_lon / count
        barycenter_lat = total_lat / count
        barycenters.append({
            "parent_station": parent_station,
            "stop_name": stop_name,
            "barycenter_lon": barycenter_lon,
            "barycenter_lat": barycenter_lat
        })
    
    return barycenters

# @app.get("/barycenters")
# async def get_barycenters():
#     # Fetch all stops
#     stops = await Stop.all()
    
#     # Group stops by parent_station
#     grouped_stops = {}
#     for stop in stops:
#         parent_station = stop.parent_station
#         if parent_station not in grouped_stops:
#             grouped_stops[parent_station] = []
#         grouped_stops[parent_station].append(stop)
    
#     # Calculate the barycenter for each parent station
#     barycenters = []
#     for parent_station, stop_group in grouped_stops.items():
#         if not parent_station:  # Skip if there is no parent station
#             continue
        
#         total_lon = sum(stop.stop_lon for stop in stop_group)
#         total_lat = sum(stop.stop_lat for stop in stop_group)
#         stop_name = stop_group[0].stop_name
#         count = len(stop_group)
#         barycenter_lon = total_lon / count
#         barycenter_lat = total_lat / count
        
#         # Retrieve route_color and route_text_color
#         parent_stop = stop_group[0]
#         stop_times = await StopTime.filter(stop=parent_stop.stop_id).prefetch_related('trip')
#         if stop_times:
#             trip = stop_times[0].trip
#             route = await Route.get(route_id=trip.route_id)
#             route_color = route.route_color
#             route_text_color = route.route_text_color
#         else:
#             route_color = None
#             route_text_color = None

#         barycenters.append({
#             "parent_station": parent_station,
#             "stop_name": stop_name,
#             "barycenter_lon": barycenter_lon,
#             "barycenter_lat": barycenter_lat,
#             "route_color": route_color,
#             "route_text_color": route_text_color,
#         })
    
#     return barycenters

@app.get("/stop_times")
async def get_stop_times(trip_id: Optional[str] = Query(None)):
    if trip_id:
        stop_times = await StopTime.filter(trip__trip_id=trip_id).prefetch_related("trip", "stop").order_by("stop_sequence").all()
    else:
        stop_times = await StopTime.all().prefetch_related("trip", "stop")
    return [
        {
            "trip_id": stop_time.trip.trip_id,
            "arrival_time": stop_time.arrival_time,
            "departure_time": stop_time.departure_time,
            "stop_id": stop_time.stop.stop_id,
            "stop_sequence": stop_time.stop_sequence,
            "pickup_type": stop_time.pickup_type,
            "drop_off_type": stop_time.drop_off_type,
            "local_zone_id": stop_time.local_zone_id,
            "stop_headsign": stop_time.stop_headsign,
            "timepoint": stop_time.timepoint,
        }
        for stop_time in stop_times
    ]

@app.get("/transfers")
async def get_transfers(from_stop_id: Optional[str] = Query(None), to_stop_id: Optional[str] = Query(None)):
    if from_stop_id and to_stop_id:
        transfers = await Transfer.filter(from_stop__stop_id=from_stop_id, to_stop__stop_id=to_stop_id).prefetch_related("from_stop", "to_stop").all()
    elif from_stop_id:
        transfers = await Transfer.filter(from_stop__stop_id=from_stop_id).prefetch_related("from_stop", "to_stop").all()
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
        pathways = await Pathway.filter(from_stop__stop_id=from_stop_id, to_stop__stop_id=to_stop_id).prefetch_related("from_stop", "to_stop").all()
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

    stop_times = await StopTime.filter(trip__trip_id=trip_id).prefetch_related("trip", "stop").order_by("stop_sequence").all()

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

@app.get("/shortest_path")
async def get_shortest_path():
    return {"message": "Shortest Path"}

# -----------------------------------------------------------------------------
#                       NETWORK CONNECTIVITY CHECK
# -----------------------------------------------------------------------------

@app.get("/connectivity")
async def check_connectivity():
    return {"message": "Connectivity Check"}

# -----------------------------------------------------------------------------
#                       MINIMUM SPANNING TREE (Kruskal)
# -----------------------------------------------------------------------------

@app.get("/minimum_spanning_tree")
async def get_minimum_spanning_tree():
    return {"message": "Minimum Spanning Tree"}

# -----------------------------------------------------------------------------
#                       RUN THE APP
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)