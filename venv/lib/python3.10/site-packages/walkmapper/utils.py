import datetime
import os
import re
import shutil
import datetime
import time
import collections
import sys

import matplotlib.pyplot as plt
import matplotlib.animation as manimation
import gpxpy
import numpy as np
import pandas as pd


def haversine(l_1, l_2):
    '''
    Calculates haversine of angle

    Parameters
    -----------
    l_1: latitude or longitude of first point (in radians)
    l_2: latitude or longitude of second point (in radians)

    Returns
    ----------
    haversine of angle
    '''
    return (1 - (np.cos(l_2 - l_1))) / 2.0


def calculate_distance(lat_1, lon_1, lat_2, lon_2):
    '''
    Employs haversine function to calculate distance between two points

    Parameters
    -----------
    lat_1: latitude of first point
    lon_1: longitude of first point
    lat_2: latitude of second point
    lon_2: longitude of second point

    Returns
    -----------
    distance between two coordinates in meters
    '''
    lat_1 = np.radians(lat_1)
    lon_1 = np.radians(lon_1)
    lat_2 = np.radians(lat_2)
    lon_2 = np.radians(lon_2)

    r = 6367303     # radius at ~45.5 degree latitude (m)
    return 2 * r * np.arcsin(np.sqrt(haversine(lat_1, lat_2) + np.cos(lat_1) * np.cos(lat_2) * haversine(lon_1, lon_2)))


def map_file_name(current_map_file_path, ur_lat, ur_lon, ll_lat, ll_lon, description=None):
    '''
    Renames an existing map image based on lower-left-corner and upper-right-corner lats/lons

    Parameters
    -----------
    current_map_file_path: current file path to image of interest
    ur_lat: latitude of upper right corner of map image
    ur_lon: longitude of upper right corner of map image
    ll_lat: latitude of lower left corner of map image
    ll_lon: longitude of lower left corner of map image
    description: optional brief description of the map (e.g.: 'Portland')

    Returns
    -----------
    Function does not return anything, instead copies and renames the image file
    '''

    # parsing the absolute path, the file name, and the extension of the image file
    absolute_path = os.path.split(os.path.abspath(current_map_file_path))[0]
    file_name, extension = os.path.splitext(
        os.path.basename(current_map_file_path))

    new_file_name = ''      # for building our new file name

    # add in the optional description
    if description:
        description = description.split(' ')
        append_description = ''
        for i in description:
            append_description += i.capitalize()
        new_file_name += append_description + '_'

    # incorporating the lat/lons of the upper right and lower left corners

    # upper right latitude
    if ur_lat < 0:
        new_file_name += f'm{abs(ur_lat)}_'
    else:
        new_file_name += str(ur_lat) + '_'

    # upper right longitude
    if ur_lon < 0:
        new_file_name += f'm{abs(ur_lon)}_'
    else:
        new_file_name += str(ur_lon) + '_'

    # lower left latitude
    if ll_lat < 0:
        # 'm' used as prefix for negative numbers
        new_file_name += f'm{abs(ll_lat)}_'
    else:
        new_file_name += str(ll_lat) + '_'

    # lower left longitude
    if ll_lon < 0:
        new_file_name += f'm{abs(ll_lon)}'
    else:
        new_file_name += str(ll_lon)

    new_file_name += extension  # add back the extension

    new_file_path = os.path.join(
        absolute_path, new_file_name)  # final path name

    # copy the image at the current path and save it with the new path name
    shutil.copy(os.path.abspath(current_map_file_path), new_file_path)


def bound_box_from_map(map_file_path):
    '''
    Parses map file name to extract bounding box (map file should have been named with map_file_name function)

    Parameters
    -----------
    map_file_path: path to map file

    Returns
    -----------
    bounding box as a tuple
    '''
    try:
        map_file_path = os.path.splitext(map_file_path)[0].split('_')
        temp_bound_box = [map_file_path[-1], map_file_path[-3],
                          map_file_path[-2], map_file_path[-4]]
    except IndexError:
        print('Error: please make sure map title has format Description_UpperRightLat_UpperRightLon_LowerLeftLat_LowerLeftLon.png')
        raise
    bound_box = []
    for i in temp_bound_box:
        try:
            bound_box.append(float(i))
        except:
            bound_box.append(-1 * float(i[1:]))

    return tuple(bound_box)


def gpx_to_dataframe(file_name, time_delta):
    '''
    Converts a GPX file to a pandas dataframe

    Parameters
    -----------
    file_name: path/file name of the GPX file
    time_delta: difference in hours between your timezone and UTC (-7 is PST)

    Returns
    -----------
    pandas dataframe containing time/longitued/latitude data
    '''
    # open and parse the GPX file
    with(open(file_name)) as f:
        gpx_file_data = gpxpy.parse(f)

    # arrays for storing data
    times = []
    longitudes = []
    latitudes = []

    # iterate through the GPX file and append data to arrays
    for track in gpx_file_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                point.adjust_time(datetime.timedelta(
                    hours=time_delta))  # time is natively UTC
                times.append(point.time)
                longitudes.append(point.longitude)
                latitudes.append(point.latitude)

    return pd.DataFrame(data={'Time': times,
                              'Longitude': longitudes,
                              'Latitude': latitudes})


def route_distance(gpx_file_df):
    '''
    Calculates the distance traversed in a GPX file

    Parameters
    -----------
    gpx_file_df: GPX data already in a pandas dataframe

    Returns
    -----------
    total distance traversed in GPX data set
    '''
    lons = gpx_file_df['Longitude']
    lats = gpx_file_df['Latitude']

    distance = [calculate_distance(
        lats[i - 1], lons[i - 1], lats[i], lons[i]) for i in range(1, len(lons))]
    # converting from meters to miles and returning
    return round(sum(distance) * 0.000621371, 3)


def date_time_stamp():
    '''
    Creates a date/time stamp for file names (takes local time from your machine)
    '''
    t = datetime.datetime.fromtimestamp(time.time())
    return t.strftime('%Y%m%d_%H%M%S')

def frames_in_route(route, frame_distance):
    '''
    Calculates the number of frames used to animate a route

    Parameters
    -----------
    route: a SingleRoute
    frame_distance: distance that the path extends each frame
    '''
    counter = 0     # number of data points counted
    distance_traveled = 0       # distance traveled this frame
    frames = 0     # total number of frames counted

    while counter < len(route):
        while distance_traveled < frame_distance and counter < len(route):
            if counter > 0:
                # add the distance between this point and the last to the distance traveled this leg
                distance_traveled += calculate_distance(route.data['Latitude'].iloc[counter],
                                                        route.data['Longitude'].iloc[counter],
                                                        route.data['Latitude'].iloc[counter - 1],
                                                        route.data['Longitude'].iloc[counter - 1])
            counter += 1

        distance_traveled = 0 # reset distance traveled
        frames += 1

    # there is one more frame used to change the color of previously rendered routes
    frames += 1
    return frames

def show_frames_done(frames_done, total_frames):
    sys.stdout.write(f'\rRendered frame {frames_done} out of {total_frames}')
    sys.stdout.flush()

def snake_animation(route_or_routes,
                    frame_distance,
                    map_file_path,
                    fps,
                    dpi,
                    marker_size,
                    active_color,
                    set_color,
                    post_pause,
                    path_to_ffmpeg):
    '''
    **This is a private implementation and not meant to be used directly.
    Use either SingleRoute.snake_animation or MultipleRoutes.snake_animation.**

    Creates a .mp4 video wherein each route is "crawled" through by a distance frame_distance in
     each frame. It is suggested that this is only used for a few routes at a time. It is still
     in the process of being optimized...

    Parameters
    -----------
    route_or_routes: either a SingleRoute, or a list of SingleRoute
    frame_distance: distance that the path extends each frame
    map_file_path: path to a map image, which will be displayed beneath the plot 
     (map file name should be created using utils.map_file_name function)
    fps: frames per second of video (each gpx data point is one frame)
    dpi: resolution of each image in video
    marker_size: size of plotted routes
    active_color: color that each new route is displayed in
    set_color: color that each route takes after its debut frame
    post_pause: time (in seconds) that the last frame is paused on (good for Instagram,
      or other platforms with autoloops)
    path_to_ffmpeg: path to ffmpeg writer on your machine
    '''
    # check if route_or_routes is a single route, and if so convert it to an iterable (tuple)
    if isinstance(route_or_routes, list):
        route_iterable = route_or_routes
        routes_count = len(route_iterable)
    else:
        route_iterable = (route_or_routes,)
        routes_count = 1

    # set the path to FFMPEG (this should be stored in ./constants.py)
    plt.rcParams['animation.ffmpeg_path'] = path_to_ffmpeg
    ffmpeg_writer = manimation.writers['ffmpeg']
    writer = ffmpeg_writer(fps=fps)

    fig, ax = plt.subplots()
    plt.axis('off')

    # if the user includes a map background, plot it w/ bounding box
    # bounding box values are parsed from map file name
    if map_file_path:
        bound_box = bound_box_from_map(map_file_path)
        img = plt.imread(map_file_path)
        ax.imshow(img, zorder=0, extent=bound_box, aspect='auto')
        ax.set_xlim(bound_box[0], bound_box[1])
        ax.set_ylim(bound_box[2], bound_box[3])

    with writer.saving(fig, f'{date_time_stamp()}.mp4', dpi):
        # loop through the routes...
        for index, route in enumerate(route_iterable):
            print(f'Rendering route {index + 1} of {routes_count}')

            plt.title(route.date)
            counter = 0     # number of data points counted
            distance_traveled = 0       # distance traveled this frame
            frames_done = 0       # number of frames already rendered
            total_frames = frames_in_route(route, frame_distance)

            while counter < len(route):
                # create lists for storing current leg data
                leg_latitudes = []
                leg_longitudes = []

                # append data to leg lists
                while distance_traveled < frame_distance and counter < len(route):
                    leg_latitudes.append(route.data['Latitude'].iloc[counter])
                    leg_longitudes.append(route.data['Longitude'].iloc[counter])

                    if counter > 0:
                        # add the distance between this point and the last to the distance traveled this leg
                        distance_traveled += calculate_distance(route.data['Latitude'].iloc[counter],
                                                                route.data['Longitude'].iloc[counter],
                                                                route.data['Latitude'].iloc[counter - 1],
                                                                route.data['Longitude'].iloc[counter - 1])
                    counter += 1

                # scatter plot the current leg
                ax.scatter(leg_longitudes, leg_latitudes,
                           zorder=1, color=active_color, s=marker_size)

                writer.grab_frame()
                frames_done += 1
                show_frames_done(frames_done, total_frames)
                distance_traveled = 0   # reset distance traveled

            # scatter all previous legs in set color
            ax.scatter(route.data['Longitude'],
                       route.data['Latitude'], zorder=1, color=set_color, s=marker_size)
            writer.grab_frame()
            frames_done += 1
            show_frames_done(frames_done, total_frames)

            print() # add final newline

        # post pause on last frame
        frames_done = 0
        total_frames = int(post_pause * fps)
        print('Rendering pause on last frame')
        for i in range(total_frames):
            writer.grab_frame()
            frames_done += 1
            show_frames_done(frames_done, total_frames)

        print() # add final newline
