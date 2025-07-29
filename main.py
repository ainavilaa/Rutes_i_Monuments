from yogi import read
from segments import *
from graphmaker import *
from viewer import *
from monuments import * 
from routes import *

# Catalonia's approx bounding box Region
CAT_BOUNDS = {
    "min_lat": 40.5,
    "max_lat": 42.9,
    "min_lon": 0.15,
    "max_lon": 3.33
}

def _read_float() -> float:
      '''Read an input. 
      If it is a float, return the value.
      If not, print en error message.'''
      try: 
            value = read(float)
            return value
      except ValueError:
            raise ValueError("It isn't a valid input... Please try again!")

def _catalan_region(lat: float, lon: float) -> bool:
      '''Check if a given point is within catalonia boundaries'''
      return (CAT_BOUNDS["min_lat"] <= lat <= CAT_BOUNDS["max_lat"] and
                  CAT_BOUNDS["min_lon"] <= lon <= CAT_BOUNDS["max_lon"])

def _in_selected_region(region: Region, point: Point) -> bool:
      '''Check if a given point is in the selected region'''
      min_lat = min(region.bottom_left.lat, region.top_right.lat)
      max_lat = max(region.bottom_left.lat, region.top_right.lat)
      min_lon = min(region.bottom_left.lon, region.top_right.lon)
      max_lon = max(region.bottom_left.lon, region.top_right.lon)
      return (min_lat <= point.lat <= max_lat and min_lon <= point.lon <= max_lon)

def _read_cluster_num() -> int:
      '''Read an input.
      If it is valid, return the value.
      If not, print an error message''' 
      try:
            clust_num = read(int)
            if clust_num <= 1:
                  raise ValueError("The cluster number must be higher than 1.")
            return clust_num
      except ValueError:
            raise ValueError("This cluster number is not valid. Please enter a valid number greater than 1.")

def _read_epsilon() -> float:
      '''Read an input for the epsilon value.
      If it is valid, return the value.
      If not, print an error message'''
      try:
            epsilon = read(float)
            if epsilon > 25:
                   raise ValueError("The epsilon value has to be smaller.")
            return epsilon
      except ValueError:
            raise ValueError("This epsilon value is not valid.")

def _read_str() -> str:
      '''Read an input for a filename.
      If it is valid, return the value.
      If not, print an error message'''
      while True:
            name = read(str)
            if name:
                  return name
            else:
                  print("We need a filename, the input can't be empty!")

def main() -> None:
      print("Hello! Wellcome to our hiking routes app!")
      print("Here, you'll be able to discover and explore the the hidden trails and medieval gems of any region.")
      print("To get started and enhance your experience we need you to give us some information.")
    
      print("Which are the geographic coordinates of your region of interest?")
      print("Please enter the latitude and the longitude for the first point.")
      lat1, lon1 = _read_float(), _read_float()
      print("Now the same for the second point")      
      lat2, lon2 = _read_float(), _read_float()
      reg = Region(Point(lat1, lon1), Point(lat2, lon2))
      reg_OSM = Region(Point(lon1, lat1), Point(lon2, lat2))

      if not (_catalan_region(lat1, lon1) and _catalan_region(lat2, lon2)):
            print("Hey, you've given coordinates that are not within Catalan territory.")
            return
      
      print("Do you already have a file with the segments in the region you have introduced?")
      print("If your answer is yes, please type the filename and make sure that it is located at the same script and don't introduce the extension.") 
      print("Otherwise, don't worry. We'll create a new file with the name you introduce.")
      segment_filename = _read_str()
      txt_segment_filename = segment_filename + ".txt"
      seg = get_segments(reg_OSM, txt_segment_filename) # Segments list to process

      print("Write another filename to get the representation of the segments in your region of interest.")
      seg_rep_filename = _read_str()
      png_seg_rep_filename = seg_rep_filename + ".png"
      show_segments(seg, png_seg_rep_filename)

      print("Do you already have a file with the monuments in the region you have introduced?")
      print("If your answer is yes, please type the filename and make sure that it is located at the same script and don't introduce the extension.") 
      print("Otherwise, don't worry. We'll create a new file with the name you introduce.")
      monuments_filename = _read_str()
      txt_monuments_filename = monuments_filename + ".txt"
      get_monuments(txt_monuments_filename)
      
      print('How many clusters do you want for clustering?')
      clusters = _read_cluster_num()
      print('At what epsilon value do you want us to consider a delatable segment?')
      epsilon = _read_epsilon()
      print('Last thing, please type the starting point for the route.')
      start_lat, start_lon = _read_float(), _read_float()
      start = Point(start_lat, start_lon)

      if not (_in_selected_region(reg, start)):
            print("The starting point is not in catalan land.")
            return
      
      print("Finally, please specify the file you want to save your 2D and 3D maps.")
      map_filename = _read_str()
      png_filename = map_filename + ".png"
      kml_filename = map_filename + ".kml"

      print("Thank you! We are processing your details. This may take a few minutes, please don't turn off your device.")
      global_graph, selected_monuments = make_graph(seg, clusters, epsilon, reg, start, txt_monuments_filename)
      route_graph = create_route_graph(global_graph, 'start', selected_monuments)

      print("The routes to all the accessible monuments have been created:")
      find_routes(route_graph, Point(start_lat, start_lon), selected_monuments)

      print("In a few minutes you'll be ready to see your maps!")
      export_PNG(route_graph, png_filename, reg)
      export_KML(route_graph, kml_filename)
      print("Your maps are ready! You can find them in the same directory as this script.")
      print("Enjoy your hiking experience!")

if __name__ == "__main__":
      main()
      