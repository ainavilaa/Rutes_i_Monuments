import networkx as nx
from math import *
import haversine as hs
from typing import *
from sklearn.cluster import KMeans
import numpy as np
from numpy.typing import NDArray
from dataclasses import *
from segments import Point, Segments,Region  
from haversine import haversine, Unit
from monuments import select_monuments_in_region, Monuments

def make_graph(segments: Segments, clusters: int, epsilon: float, region: Region, start: Point, filename: str) -> nx.Graph:
    """Make a graph from the segments."""
    
    # Convert segments to a numpy array of points
    seg_array = np.array(
        [
            [point.lat, point.lon]
            for segment in segments
            for point in [segment.start, segment.end]
        ],
        dtype=np.float64,
    )

    # Clustering on points
    clustering = KMeans(n_clusters=clusters, random_state=0, n_init="auto")
    clustering.fit(seg_array)
    cluster_labels = clustering.labels_

    # Create graph with cluster centroids as nodes
    G = nx.Graph()
    centroids = clustering.cluster_centers_
    for num, centroid in enumerate(centroids):
        G.add_node(num, pos=(centroid[0], centroid[1]), type="others") 

    centroids_adj: dict[tuple[int, int], int] = {}
    # Count adjacencies between points from the same segment and different centroid
    for index in range(0, len(cluster_labels), 2):
        if cluster_labels[index] != cluster_labels[index + 1]:
            x = min(cluster_labels[index], cluster_labels[index + 1])
            y = max(cluster_labels[index], cluster_labels[index + 1])
            if (x, y) not in centroids_adj.keys():
                centroids_adj[(x, y)] = 0
            centroids_adj[(x, y)] += 1
    
    # Valid adjacencies
    for (x, y), value in centroids_adj.items():
        if value > 0:
            G.add_edge(x, y)
    _simplify_graph(G, epsilon)
    selected_monuments = select_monuments_in_region(region, filename)
    _add_monuments_to_graph(G, selected_monuments)
    _add_start_node(G, start)
    return G, selected_monuments

def _simplify_graph(graph: nx.Graph, epsilon: float) -> nx.Graph:
    """Simplify the graph."""
    simple_G = nx.Graph()

    # Add nodes to simple graph
    for node in graph.nodes():
        simple_G.add_node(node)
    # Straight path candidates
    candidates: set[tuple[Any, Any, Any]] = set()
    for node in graph.nodes():
        if graph.degree[node] == 2:
            neighbors = list(graph.neighbors(node))
            candidates.add((node, neighbors[0], neighbors[1]))

    # Straight path analysis
    for g2, g1, g3 in candidates:
        angle = _calc_angle(
            graph.nodes[g1]["pos"], graph.nodes[g2]["pos"], graph.nodes[g3]["pos"]
        )
        if abs(180 - angle) < epsilon:
            if not simple_G.has_edge(g1, g3):
                simple_G.add_edge(g1, g3)
        else:
            if not simple_G.has_edge(g1, g2):
                simple_G.add_edge(g1, g2)
            if not simple_G.has_edge(g2, g3):
                simple_G.add_edge(g2, g3)

    return simple_G

def _calc_angle(p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> float:
    """Calculate the angle in degrees between p1-p2-p3"""

    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])

    dot_product = np.dot(v1, v2)
    lenght1 = np.linalg.norm(v1)
    lenght2 = np.linalg.norm(v2)
    cos = dot_product / (lenght1 * lenght2)
    cos_angle = np.clip(
        cos, -1.0, 1.0
    )  # Avoid numerical precision issues for floating-point

    # Angle in radians
    a_rad = np.arccos(cos_angle)
    # Degree convertion
    angle = np.degrees(a_rad)
    return angle


def _add_monuments_to_graph(G: nx.Graph, monuments: Monuments):
    '''Add the monuments of a list in the graph'''
    
    for monument in monuments:
        name, point = monument.name, monument.location
        lat, lon = point.lat, point.lon
        G.add_node(name, pos=point, type="monument")
        nearest_node = _find_nearest_node(Point(lat, lon), G)
        G.add_edge(name, nearest_node)


def _add_start_node(G: nx.Graph, start_point: Point):
    '''Add the given starting point to the graph'''
    
    G.add_node("start", pos=start_point, type="start")
    lat, lon = start_point.lat, start_point.lon
    nearest_node = _find_nearest_node(Point(lat, lon), G)
    G.add_edge("start", nearest_node)


def _find_nearest_node(point: Point, G: nx.Graph):
    '''Given a point, find the nearest node in the graph'''
    
    latitude, longitude = point.lat, point.lon
    min_distance = float("inf")
    nearest_node = None

    for node, data in G.nodes(data=True):
        if data.get("type") != "others":
            continue
        node_lat_lon = (
            (data["pos"].lat, data["pos"].lon)
            if isinstance(data["pos"], Point)
            else data["pos"]
        )
        distance = haversine((latitude, longitude), node_lat_lon, unit=Unit.METERS)

        if distance < min_distance:
            min_distance = distance
            nearest_node = node

    return nearest_node


def create_route_graph(G: nx.Graph, start_node: str, selected_monuments: Monuments):
    '''Given the corresponding graph with a starting point 
    and a list of monuments, create a route'''
    route_graph = nx.Graph()

    # Añadir el nodo de inicio con el tipo 'start'
    route_graph.add_node(start_node, pos=G.nodes[start_node]["pos"], type="start")

    for monument in selected_monuments:
        monument_node = monument.name 
        if start_node in G and monument_node in G:
            if nx.has_path(G, start_node, monument_node):
                path = nx.shortest_path(G, start_node, monument_node)
                for i in range(len(path) - 1):
                    route_graph.add_edge(path[i], path[i + 1])
                    route_graph.nodes[path[i]]["pos"] = G.nodes[path[i]]["pos"]
                    route_graph.nodes[path[i + 1]]["pos"] = G.nodes[path[i + 1]]["pos"]
                    if path[i] != start_node and path[i] not in [m.name for m in selected_monuments]:
                        route_graph.nodes[path[i]]["type"] = "others"
    
            # Add the node monument with the type 'monument'
            route_graph.add_node(monument_node, pos=G.nodes[monument_node]["pos"], type="monument")
    return route_graph

