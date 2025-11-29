import os
from math import radians

import matplotlib.pyplot as plt
import matplotlib.animation as manimation
import numpy as np
import pandas as pd

from walkmapper.utils import *


class SingleRoute:
    '''
    Class for analyzing/plotting a single GPX data file

    Parameters
    -----------
    gpx_file_path: path to the GPX file of interest
    home_lat: latitude of home, if privacy bubble is to be used (do not select your exact home coords)
    home_lon: longitude of home, if privacy bubble is to be used (do not select your exact home coords)
    privacy_bubble_rad: radius of privacy bubble (in meters), if privacy bubble is to be used
    '''

    def __init__(self, gpx_file_path, home_lat=None, home_lon=None, privacy_bubble_rad=None, time_delta=-7):
        self.gpx_file_path = gpx_file_path
        self.time_delta = time_delta

        self.data = gpx_to_dataframe(self.gpx_file_path, self.time_delta)
        self.date = self.data['Time'][0].strftime('%Y-%m-%d')
        self.distance = route_distance(self.data)

        self.home_lat = home_lat
        self.home_lon = home_lon
        self.privacy_bubble_rad = privacy_bubble_rad

        # if the user has set a privacy bubble...
        if None not in [self.home_lat, self.home_lon, self.privacy_bubble_rad]:
            # ... exclude data points within the bubble radius
            self.data = self.data.loc[calculate_distance(self.data['Latitude'],
                                                         self.data['Longitude'],
                                                         self.home_lat, self.home_lon) > self.privacy_bubble_rad]
        else:
            none_count = [self.home_lat, self.home_lon,
                          self.privacy_bubble_rad].count(None)

            # if the user entered invalid privacy bubble information, raise an error
            if none_count != 0 and none_count != 3:
                raise ValueError(
                    'Please make sure all or none of the following parameters have the value "None": home_lat, home_lon, and privacy_bubble_rad')

        # rough estimate of route duration (last minus first timestamp)
        self.duration = round((self.data['Time'].iat[-1] -
                               self.data['Time'].iat[0]).seconds / 60.0, 3)

        # distance of route (in miles)

    def __len__(self):
        '''
        Returns the number of data points in the route
        '''
        return len(self.data)

    def to_csv(self, csv_file_name):
        '''
        Convert the object data to .csv file with name csv_file_name

        Parameters
        -----------
        csv_file_name: path to .csv file
        '''
        if not csv_file_name.endswith('.csv'):
            csv_file_name += '.csv'
        self.data.to_csv(csv_file_name, index=False)

    def plot(self, map_file_path=None, marker_color='red', marker_size=0.5, show=True):
        '''
        Plots a single route and saves/displays

        Parameters
        -----------
        map_file_path: path to a map image, which will be displayed beneath the plot 
         (map file name should be created using utils.map_file_name function)
        marker_color: color that route is plotted with
        marker_size: size of marker used for plotting
        '''
        fig, ax = plt.subplots()
        ax.scatter(self.data['Longitude'],
                   self.data['Latitude'], zorder=1, c='red', s=marker_size)

        # if the user includes a map background, plot it w/ bounding box
        # bounding box values are parsed from map file name
        if map_file_path:
            bound_box = bound_box_from_map(map_file_path)
            ax.set_xlim(bound_box[0], bound_box[1])
            ax.set_ylim(bound_box[2], bound_box[3])
            img = plt.imread(map_file_path)
            ax.imshow(img, zorder=0, extent=bound_box, aspect='auto')

        plt.axis('off')

        if show:
            plt.show()

    def snake_animation(self,
                        frame_distance=50,
                        map_file_path=None,
                        fps=60,
                        dpi=300,
                        marker_size=0.5,
                        active_color='red',
                        set_color='blue',
                        post_pause=2,
                        path_to_ffmpeg='/usr/local/bin/ffmpeg'):
        '''
        Creates a .mp4 video wherein this route is "crawled" through by a distance frame_distance in
         each frame. It is still in the process of being optimized...

        Parameters
        -----------
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
        return snake_animation(self,
                               frame_distance=frame_distance,
                               map_file_path=map_file_path,
                               fps=fps,
                               dpi=dpi,
                               marker_size=marker_size,
                               active_color=active_color,
                               set_color=set_color,
                               post_pause=post_pause,
                               path_to_ffmpeg=path_to_ffmpeg)


class MultipleRoutes:
    '''
    Class for analyzing/plotting a multiple GPX data files. 
    Takes in a list of file paths and creates SingleRoute objects for each

    Parameters
    -----------
    files: a list of file paths
    home_lat: latitude of home, if privacy bubble is to be used (do not select your exact home coords)
    home_lon: longitude of home, if privacy bubble is to be used (do not select your exact home coords)
    privacy_bubble_rad: radius of privacy bubble (in meters), if privacy bubble is to be used
    '''

    def __init__(self, files, home_lat=None, home_lon=None, privacy_bubble_rad=None, time_delta=-7):

        self.home_lat = home_lat
        self.home_lon = home_lon
        self.privacy_bubble_rad = privacy_bubble_rad
        self.time_delta = time_delta

        self.files = [i for i in files if i.endswith('.gpx')]

        # convert all files into SingleRoute classes and store in a list
        self.routes = [SingleRoute(
            i, self.home_lat, self.home_lon, self.privacy_bubble_rad, self.time_delta) for i in self.files]

    def __len__(self):
        '''
        Returns the number of routes
        '''

        return len(self.routes)

    def compile_data(self):
        '''
        Compiles data from all routes into a single pandas dataframe, which is returned
        '''
        all_lats = []
        all_lons = []

        for i in self.routes:
            all_lats += list(i.data['Latitude'])
            all_lons += list(i.data['Longitude'])

        return pd.DataFrame({'Latitude': all_lats, 'Longitude': all_lons})

    def basic_plot(self,
                   map_file_path=None,
                   marker_color='red',
                   marker_size=0.5,
                   show=True,
                   save_file_path=None,
                   dpi=300):
        '''
        Plots all routes on one map

        Parameters
        -----------
        map_file_path: path to a map image, which will be displayed beneath the plot 
         (map file name should be created using utils.map_file_name function)
        marker_color: color that route is plotted with
        marker_size: size of marker used for plotting
        show: if True, will show plot upon completion
        save_file_path: path to where the image will be saved
        dpi: resolution of final image
        '''
        fig, ax = plt.subplots()

        # scatter plot all routes
        [ax.scatter(i.data['Longitude'],
                    i.data['Latitude'], zorder=1, c=marker_color, s=marker_size) for i in self.routes]

        # if the user includes a map background, plot it w/ bounding box
        # bounding box values are parsed from map file name
        if map_file_path:
            bound_box = bound_box_from_map(map_file_path)
            ax.set_xlim(bound_box[0], bound_box[1])
            ax.set_ylim(bound_box[2], bound_box[3])
            img = plt.imread(map_file_path)
            ax.imshow(img, zorder=0, extent=bound_box, aspect='auto')

        plt.axis('tight')
        plt.axis('off')
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        if save_file_path:
            if not save_file_path.endswith('.png'):
                save_file_path += '.png'

            plt.savefig(save_file_path, dpi=dpi,
                        bbox_inches='tight', pad_inches=0)
        if show:
            plt.show()

    def heat_map(self, map_file_path, n_bins=100, alpha=0.5, show=True, save_file_path=None, dpi=300):
        '''
        Plots a heat map of all routes overlaid on a map

        Parameters
        -----------
        map_file_path: path to a map image, which will be displayed beneath the plot 
         (map file name should be created using utils.map_file_name function)
        n_bins: number of bins for histogram
        alpha: transparency of heatmap
        show: if True, will show plot upon completion
        save_file_path: path to where the image will be saved
        dpi: resolution of final image
        '''
        bound_box = bound_box_from_map(map_file_path)
        dta = self.compile_data()

        fig, ax = plt.subplots()

        # the heat map is constructed from a 2D histogram
        ax.hist2d(dta['Longitude'], dta['Latitude'], n_bins, range=[
                  [bound_box[0], bound_box[1]], [bound_box[2], bound_box[3]]], alpha=alpha, zorder=1)

        ax.set_xlim(bound_box[0], bound_box[1])
        ax.set_ylim(bound_box[2], bound_box[3])
        img = plt.imread(map_file_path)
        ax.imshow(img, zorder=0, extent=bound_box, aspect='auto')
        plt.axis('off')

        if save_file_path:
            if not save_file_path.endswith('.png'):
                save_file_path += '.png'

            plt.savefig(save_file_path, dpi=dpi,
                        bbox_inches='tight', pad_inches=0)
        if show:
            plt.show()

    def basic_route_animation(self,
                              map_file_path=None,
                              fps=2,
                              dpi=300,
                              marker_size=0.5,
                              active_color='red',
                              set_color='blue',
                              post_pause=2,
                              path_to_ffmpeg='/usr/local/bin/ffmpeg'):
        '''
        Creates a .mp4 video with each separate route first appearing in active_color, and then
          transitioning to set_color. The video is saved in the current directory, the title is a 
          timestamp of when the video was saved

        Parameters
        -----------
        map_file_path: path to a map image, which will be displayed beneath the plot 
         (map file name should be created using utils.map_file_name function)
        fps: frames per second of video (each route is one frame, so fps=2 is 0.5 sec per route)
        dpi: resolution of each image in video
        marker_size: size of plotted routes
        active_color: color that each new route is displayed in
        set_color: color that each route takes after its debut frame
        post_pause: time (in seconds) that the last frame is paused on (good for Instagram,
          or other platforms with autoloops)
        path_to_ffmpeg: path to ffmpeg writer on your machine
        '''

        # set the path to FFMPEG (this should be stored in ./constants.py)
        plt.rcParams['animation.ffmpeg_path'] = path_to_ffmpeg
        ffmpeg_writer = manimation.writers['ffmpeg']
        writer = ffmpeg_writer(fps=fps)

        fig, ax = plt.subplots()

        # if the user includes a map background, plot it w/ bounding box
        # bounding box values are parsed from map file name
        if map_file_path:
            bound_box = bound_box_from_map(map_file_path)
            ax.set_xlim(bound_box[0], bound_box[1])
            ax.set_ylim(bound_box[2], bound_box[3])
            img = plt.imread(map_file_path)
            ax.imshow(img, zorder=0, extent=bound_box, aspect='auto')

        plt.axis('off')

        with writer.saving(fig, f'{date_time_stamp()}.mp4', dpi):
            counter = 0

            # loop through the routes...
            for i in range(len(self.routes)):
                # let the user know which route is being processed
                print(f'Rendering route {i + 1} of {len(self.routes)}')

                # after the first loop...
                if counter > 0:
                    # plot all old routes in set_color
                    for j in range(0, counter):
                        ax.scatter(self.routes[j].data['Longitude'], self.routes[j].data['Latitude'],
                                   zorder=1, color=set_color, s=marker_size)

                # plot current route in active_color
                ax.scatter(self.routes[i].data['Longitude'], self.routes[i].data['Latitude'],
                           zorder=1, color=active_color, s=marker_size)

                # set the title to the date that the route was completed
                plt.title(self.routes[i].date)

                # save frame and increment counter
                writer.grab_frame()
                counter += 1

            # once all routes are complete, grab another frame with the last route in set_color
            ax.scatter(self.routes[-1].data['Longitude'], self.routes[-1].data['Latitude'],
                       zorder=1, color=set_color, s=marker_size)
            writer.grab_frame()

            # add the post_pause by grabbing the last frame until the duration is met
            for i in range(int(post_pause * fps)):
                writer.grab_frame()

    def snake_animation(self,
                        frame_distance=50,
                        map_file_path=None,
                        fps=60,
                        dpi=300,
                        marker_size=0.5,
                        active_color='red',
                        set_color='blue',
                        post_pause=2,
                        path_to_ffmpeg='/usr/local/bin/ffmpeg'):
        '''
        Creates a .mp4 video wherein each route is "crawled" through by a distance frame_distance in
         each frame. It is suggested that this is only used for a few routes at a time. It is still
         in the process of being optimized...

        Parameters
        -----------
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
        return snake_animation(self.routes,
                               frame_distance=frame_distance,
                               map_file_path=map_file_path,
                               fps=fps,
                               dpi=dpi,
                               marker_size=marker_size,
                               active_color=active_color,
                               set_color=set_color,
                               post_pause=post_pause,
                               path_to_ffmpeg=path_to_ffmpeg)
