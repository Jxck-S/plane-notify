from functools import partial

import pyproj
from shapely.geometry import Point
from shapely.ops import transform


def get_circle_perimeter_coords(lat, lon, radius_km):
    """
    Generate the perimeter coordinates of a circle (buffer) around the given lat, lon.

    :param lat: Latitude of the center of the circle
    :param lon: Longitude of the center of the circle
    :param radius_km: Radius of the circle in kilometers
    :return: List of coordinates (longitude, latitude) representing the perimeter of the circle
    """
    # Define WGS84 projection (longitude, latitude)
    proj_wgs84 = pyproj.Proj(proj="longlat", datum="WGS84")

    # Define Azimuthal Equidistant Projection centered on the input lat/lon
    aeqd_proj = pyproj.Proj(proj="aeqd", lat_0=lat, lon_0=lon, x_0=0, y_0=0)

    # Create a transformer for forward and inverse projection
    transformer_to_wgs84 = pyproj.Transformer.from_proj(
        aeqd_proj, proj_wgs84, always_xy=True
    )

    # Function for transforming coordinates from projected space to WGS84
    project_to_wgs84 = partial(transform, transformer_to_wgs84.transform)

    # Create a buffer (circle) around the center point in the Azimuthal Equidistant projection
    buffer_circle = Point(0, 0).buffer(radius_km * 1000)  # Buffer in meters

    # Transform the buffer's exterior coordinates to WGS84 (longitude, latitude)
    lon_lat_coords = list(project_to_wgs84(buffer_circle).exterior.coords)

    # Swap coordinates to return them as (latitude, longitude)
    lat_lon_coords = [[lat, lon] for lon, lat in lon_lat_coords]

    return lat_lon_coords
