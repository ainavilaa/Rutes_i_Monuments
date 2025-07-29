from dataclasses import *
from typing import *
import gpxpy
import requests
import staticmap
import os
from datetime import datetime
from haversine import haversine, Unit 

@dataclass
class Point:
    """A point in latitude and longitude"""

    lat: float
    lon: float

@dataclass
class Segment:
    """Segment between two points"""

    start: Point
    end: Point

@dataclass
class Region:
    """Region defined by two points"""

    bottom_left: Point
    top_right: Point

@dataclass
class Segment_to_clean:
    """Segment between two points with track time info"""

    x: Point
    t1: int  # Date
    y: Point
    t2: int  # Date

Data: TypeAlias = list[Segment_to_clean]  # List: segment{point, time - point,time}
Segments: TypeAlias = list[Segment]  # Point,point, time
VALID_DISTANCE = 0.1  # Maximum distance allowed between segment endpoints

def _get_data(region: Region) -> Data:
    """Download segments in the request region and save them to a list[segment{point, time - point,time}]"""
    page = 0
    uncleaned_segments: Data = []
    while True:
        box = f"{region.bottom_left.lat},{region.bottom_left.lon},{region.top_right.lat},{region.top_right.lon}"
        url = (
            f"https://api.openstreetmap.org/api/0.6/trackpoints?bbox={box}&page={page}"
        )
        response = requests.get(url)  # HTTP GET request to the URL
        gpx_content = response.content.decode("utf-8")
        gpx = gpxpy.parse(gpx_content)
        if len(gpx.tracks) == 0:  # No tracks in the region
            break

        for track in gpx.tracks:
            for segment in track.segments:  # Check if all points have valid time info
                if all(point.time is not None for point in segment.points):
                    segment.points.sort(key=lambda p: p.time)  # type: ignore
                    for i in range(len(segment.points) - 1):
                        p1, p2 = segment.points[i], segment.points[i + 1]
                        if p1.time is not None and p2.time is not None:
                            uncleaned_segments.append(
                                Segment_to_clean(
                                    Point(p1.latitude, p1.longitude),
                                    _convert_time(p1.time),
                                    Point(p2.latitude, p2.longitude),
                                    _convert_time(p2.time),
                                )
                            )
                        
        page += 1

    return uncleaned_segments

def _convert_time(time: datetime) -> int:
    """Given a timestamp from the GPX file, converts it into a tuple that contains date
    Format: YearMonthDay {e.g., 20040105 for January 5 2004}"""
    date = time.strftime("%Y%m%d")
    return int(date)

def _valid_distance(segment: Segment_to_clean) -> bool:
    """Given a segment calculates the difference.
    Output: True if the distance between start and endpoint is not more than 100 m, False otherwise."""
    distance: float = haversine(
        (segment.x.lat, segment.x.lon),
        (segment.y.lat, segment.y.lon),
        unit=Unit.KILOMETERS,
    )
    return distance <= VALID_DISTANCE

def _valid_segment(segment: Segment_to_clean) -> bool:
    """Checks whether the segment is from the same route:
        - Time: same day
        - Distance: not more than 0.1 km
    """
    return segment.t1 == segment.t1 and _valid_distance(segment)

def _write_segments_to_file(uncleaned_data: Data, filename: str) -> None:
    """Check the validity of each segment from uncleaned_data list,
    Write each valid segment in the file 'filename'."""
    with open(filename, "w") as file:
        for segment in uncleaned_data:
            if _valid_segment(segment):
                file.write(
                    f"{segment.x.lat}, {segment.x.lon}, {segment.y.lat}, {segment.y.lon}\n"
                )

def _load_segments(filename: str) -> Segments:
    """Load segments from the file 'filename'"""
    segments: Segments = []
    with open(filename, "r") as file:
        for line in file:
            data = line.strip().split(",")
            start = Point(float(data[0]), float(data[1]))
            end = Point(float(data[2]), float(data[3]))
            segments.append(Segment(start, end))
    return segments

def get_segments(region: Region, filename: str) -> Segments:
    """Gets all segments from the given region.
    If filename exists, load segments from the file 'filename'.
    Oterwise, download segments in the box and save them to the file 'filename'."""
    if not os.path.exists(filename):
        uncleaned_data = _get_data(region)  # Segments list
        _write_segments_to_file(uncleaned_data, filename)

    return _load_segments(filename)

def show_segments(segments: Segments, filename: str) -> None:
    """Show all segments in a PNG file using staticmaps."""
    map = staticmap.StaticMap(800, 800)
    for segment in segments:
        line = staticmap.Line(
            [
                (segment.start.lon, segment.start.lat),
                (segment.end.lon, segment.end.lat),
            ],
            color="red",
            width=2,
        )
        map.add_line(line)
    map.render().save(filename)


