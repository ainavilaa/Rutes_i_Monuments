from dataclasses import dataclass
from typing import TypeAlias
import os
import requests
from bs4 import BeautifulSoup
from segments import Point, Region 
import re

@dataclass
class Monument:
    name: str
    location: Point

Monuments: TypeAlias = list[Monument]

def _download_monuments(filename) -> None:
    """Download monuments from Catalunya Medieval."""
    urls = [
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-militar/castells/","castell"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-militar/fortificacions-depoca-carlina/","epoca-carlina"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-militar/muralles/", "muralles"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-militar/torres/", "torre"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-civil/cases-fortes/", "casa-forta"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-civil/palaus/", "palau"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-civil/ponts/", "pont"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-civil/torres-colomer/", "torre-colomer"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-religios/basiliques/", "basilica"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-religios/catedrals/", "catedral"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-religios/ermites/", "ermita"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-religios/esglesies/", "esglesia"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-religios/esglesies-fortificades/", "esglesia-fortificada"),
        ("https://www.catalunyamedieval.es/edificacions-de-caracter-religios/monestirs/", "monestir"),
        ("https://www.catalunyamedieval.es/altres-llocs-dinteres/", "altres-llocs-dinteres")
    ]
    for url, key in urls:  
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        mons = soup.find_all(
            "li", class_= key
        )  

        for mon in mons:
            link = mon.find("a")
            href = link.get("href")
            name = link.text
            lat, lon = _get_lat_lon(href).lat, _get_lat_lon(href).lon
            
            # Save monuments to a file
            with open(filename, "a") as file:
                file.write(f"{name}, {lat}, {lon}\n")

def _load_monuments(filename: str) -> Monuments:
    """Load monuments from a file."""
    monuments: Monuments = []

    with open(filename, "r") as file:
          for line in file:
            data = line.rsplit(',', 2)
            name = data[0]
            lat, lon = float(data[1]), float(data[2])
            monuments.append(Monument(name, Point(float(lat), float(lon))))
    return monuments

def get_monuments(filename: str) -> Monuments:
    """
    Get all monuments in the box.
    If filename exists, load monuments from the file.
    Otherwise, download monuments and save them to the file.
    """
    if not os.path.exists(filename):
        _download_monuments(filename)
    return _load_monuments(filename)

def _get_lat_lon(url: str) -> Point:
    """Get the latitude and longitude of a monument from its webpage."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Find content of the script
    script_tag = soup.find("script", text=re.compile(r'var destinations = \[\'.*\'\];'))

    if script_tag:
        script_content = script_tag.string
        # Expersions to extract the coordinates
        match = re.search(r'var destinations = \[\'([0-9.]+) ([0-9.]+)\'\];', script_content)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            return Point(lat, lon)
    raise ValueError("Coordinates not found on the webpage")


def select_monuments_in_region(region: Region, filename: str) -> Monuments:
    '''Given a region select the monuments in it.'''
    selected_monuments: Monuments = []
    with open(filename, 'r') as file:
        for line in file:
            data = line.rsplit(',', 2)
            name = data[0]
            lat, lon = float(data[1]), float(data[2])
            if region.bottom_left.lat <= lat <= region.top_right.lat and region.bottom_left.lon <= lon <= region.top_right.lon:
                selected_monuments.append((Monument(name, Point(lat, lon))))
    return selected_monuments



