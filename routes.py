from segments import Segment, Segments, Point, Region 
from monuments import Monuments, Monument
import networkx as nx
from dataclasses import dataclass
import staticmap
from haversine import haversine, Unit
from graphmaker import _find_nearest_node
from math import *
import haversine as hs
from typing import *
from sklearn.cluster import KMeans
import numpy as np
from numpy.typing import NDArray
from dataclasses import *


def find_routes(graph: nx.Graph, start: Point, endpoints: Monuments) -> None:
    """Find the shortest route between the starting point and all the endpoints."""

    start_node = _find_nearest_node(start, graph)
    any_route = False
    for monument in endpoints: 
        end_node = _find_nearest_node(monument.location, graph)
        route = _find_shortest_path(graph, start_node, end_node)
        if route is not None:
            any_route = True
            print(f"Monument: {monument.name}, Route: {route}") 
        
    if not any_route:
        print("There is not any monument accesible in the region from the starting point.")



def _find_shortest_path(graph: nx.Graph, start_node: Any, end: Point) -> list:
    """Find the shortest path between two points in a graph."""
    # Find the nearest nodes to the start and end points

    try:
        # Use Dijkstra's algorithm to find the shortest path
        shortest_path = nx.dijkstra_path(graph, start_node, end)
        return shortest_path
    except nx.NetworkXNoPath:
        print(f"No path between {start_node} and {end}")
        return []



