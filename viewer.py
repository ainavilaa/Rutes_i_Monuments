import networkx as nx
import staticmap
from segments import Region, Point
import simplekml


def export_PNG(graph: nx.Graph, filename: str, region: Region) -> None:
    '''Export the graph to a PNG file using staticmaps.'''
    map_center = _center_calc(region)

    m = staticmap.StaticMap(1024, 768)

    node_types = {'start': {'color': 'green', 'size': 12}, 
                  'monument':{'color': 'gold', 'size': 15},
                  'others': {'color': 'black', 'size': 12}}

    # Add nodes
    for node, coord in graph.nodes(data=True):
        if coord is None or 'pos' not in coord: 
            continue # Skip processing the node
        point = coord['pos']
        if isinstance(point, tuple):
            y, x = point  
        else:
            y, x = point.lat, point.lon  
        n_type = coord.get('type', 'others')
        m_type = node_types[n_type]
        
        m.add_marker(staticmap.CircleMarker((x, y), m_type['color'], m_type['size'])) 
   
    # Add edges
    for edge in graph.edges():
        start_n, end_n = graph.nodes[edge[0]]['pos'], graph.nodes[edge[1]]['pos']
        if isinstance(start_n, tuple):
            start_x, start_y = start_n  
        else:
            start_x, start_y = start_n.lon, start_n.lat  
        if isinstance(end_n, tuple):
            end_x, end_y = end_n    
        else:
            end_x, end_y = end_n.lon, end_n.lat 

        # Make sure that the maximum value always goes first
        start_x, start_y = min(start_x, start_y), max(start_x, start_y)
        end_x, end_y = min(end_x, end_y), max(end_x, end_y)

        m.add_line(staticmap.Line([(start_x, start_y), (end_x, end_y)], 'blue', 3))  
        
    img = m.render(zoom=11, center=(map_center.lon, map_center.lat))  
    img.save(filename)         

def _center_calc(region: Region) -> Point:
    '''Calculate the center (average lat and lon) of the given region'''
    lat = (region.bottom_left.lat + region.top_right.lat) / 2
    lon = (region.bottom_left.lon + region.top_right.lon) / 2
    return Point(lat, lon)

def export_KML(graph: nx.Graph, filename: str) -> None:
    """Export the graph to a KML file."""
    kml = simplekml.Kml()
    folder = kml.newfolder(name='Cultural Routes')
    for node, coord in graph.nodes(data=True):
        n_type = coord.get("type", "others")
        point = coord['pos']
        if isinstance(point, tuple):
            x, y = point
        else:
            x, y = point.lon, point.lat
        x, y = min(x, y), max(x, y)
        placemark = folder.newpoint(name=f"{node}", coords=[(x, y)])
    
        if n_type == 'monument':
            icon_url = 'https://maps.google.com/mapfiles/kml/pal4/icon47.png'
        elif n_type == 'others':
            icon_url = 'https://maps.google.com/mapfiles/kml/shapes/shaded_dot.png'
        else:
            icon_url = 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png'
        placemark.style.iconstyle.icon.href = icon_url

    for edge in graph.edges():
        start_n, end_n = edge
        start_coords, end_coords = graph.nodes[start_n]['pos'], graph.nodes[end_n]['pos']
        if isinstance(start_coords, tuple):
            start = (start_coords[1], start_coords[0])  # Swap the order
        else:
            start = (start_coords.lon, start_coords.lat)  # Swap the order
        if isinstance(end_coords, tuple):
            end = (end_coords[1], end_coords[0])  # Swap the order
        else:
            end = (end_coords.lon, end_coords.lat)  # Swap the order
        linestring = folder.newlinestring(coords=[start, end])
        linestring.style.linestyle.color = simplekml.Color.blue
    kml.save(filename)

