import datetime
from db_config.models import Route, Trip, StopTime
from services.graph import *

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