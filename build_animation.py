#import libraries
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import LineString, MultiLineString
from matplotlib.animation import FuncAnimation, PillowWriter
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

# set-up
data_folder = "../data/"
output_file = "../output/2025_routes.gif"
logo_path = "../logo.png"
step_duration = 0.5  # seconds per step
colors = {"ride.gpx": "#0072B2", "hike.gpx": "#2E6F40"}  
month_names = ['January','February','March','April','May','June','July',
               'September','October','November','December']  # August missing

# Hardcoded distances for the label
monthly_distances = {
    0: 14.3,   
    1: 14.2,   
    2: 10.9,   
    3: 50.8,   
    4: 14.2,   
    5: 44.9,   
    6: 10.6,  
    7: 45.6,   
    8: 30.8,   
    9: 12.3,   
    10: 11.8   
}

# Protection agains and gaps in the lines in the gpx files
def explode_multilines(geom):
    if isinstance(geom, LineString):
        return [geom]
    elif isinstance(geom, MultiLineString):
        return list(geom.geoms)
    else:
        return []


# Load the folders that contain the gpx files
month_folders = sorted([f for f in os.listdir(data_folder) 
                        if os.path.isdir(os.path.join(data_folder, f))])

all_routes = []
month_indices = []

#loop through month folders to get files
for month_idx, month in enumerate(month_folders):
    month_path = os.path.join(data_folder, month)
    gpx_files = [f for f in os.listdir(month_path) if f.endswith(".gpx")]
    print(f"{month}: {gpx_files}")
    
    #load files
    for gpx_file in gpx_files:
        gpx_path = os.path.join(month_path, gpx_file)
        gdf = gpd.read_file(gpx_path, layer='tracks')
        if gdf.empty:
            continue
        gdf['source_file'] = gpx_file
        all_routes.append(gdf)
        month_indices.extend([month_idx]*len(gdf))
#error if folder is empty
if not all_routes:
    raise ValueError(f"No GPX tracks found in {data_folder}")

#put all files into one geodataframe
all_gdfs = gpd.GeoDataFrame(pd.concat(all_routes, ignore_index=True), crs="EPSG:4326")
all_gdfs = all_gdfs.to_crs(epsg=3857)
all_gdfs['month_idx'] = month_indices


# Create the actual map
fig, ax = plt.subplots(figsize=(10, 10))
ax.axis('off')  # remove axes / ticks

# Plot limits to cover all tracks
xlim = (all_gdfs.total_bounds[0] - 500, all_gdfs.total_bounds[2] + 500)
ylim = (all_gdfs.total_bounds[1] - 500, all_gdfs.total_bounds[3] + 500)
ax.set_xlim(xlim)
ax.set_ylim(ylim)

# add basemap from contextily library in CartoDB.Voyager style
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)

# Add image (logo)
if os.path.exists(logo_path):
    logo_img = Image.open(logo_path)
    imagebox = OffsetImage(logo_img, zoom=0.4)  # adjust zoom for large logo
    ab = AnnotationBbox(imagebox, (0.02, 0.98), xycoords='axes fraction', frameon=False,
                        box_alignment=(0, 1), zorder=3)
    ax.add_artist(ab)

# Add stats in a cream box using matplotlib
lines_to_draw = []
month_totals = [0]*len(month_names)
cum_total = 0

# Box design
box_x = 0.55 
box_y = 0.72
box_width = 0.40
box_height = 0.25
padding = 0.02
bbox = FancyBboxPatch(
    (box_x, box_y),
    box_width, box_height,
    boxstyle=f"round,pad={padding}",
    transform=ax.transAxes,
    facecolor='#FDF1D6',  
    edgecolor='#333333',
    linewidth=1.5,
    zorder=2
)
ax.add_patch(bbox)

# add text to the box
text_y_positions = [0.95, 0.90, 0.86, 0.82, 0.76]  # top to bottom
text_handles = {
    "title": ax.text(box_x + box_width - 0.01, text_y_positions[0], "2025 Adventures", transform=ax.transAxes, ha='right', va='top', fontsize=16, weight='bold', color='black'),
    "month": ax.text(box_x + box_width - 0.01, text_y_positions[1], "", transform=ax.transAxes, ha='right', va='top', fontsize=14, color='black'),
    "month_dist": ax.text(box_x + box_width - 0.01, text_y_positions[2], "", transform=ax.transAxes, ha='right', va='top', fontsize=14, color='black'),
    "cum_dist": ax.text(box_x + box_width - 0.01, text_y_positions[3], "", transform=ax.transAxes, ha='right', va='top', fontsize=14, color='black'),
    "key": ax.text(box_x + box_width - 0.01, text_y_positions[4], "Green = Hike | Blue = Cycle", transform=ax.transAxes, ha='right', va='top', fontsize=10, color='black')
}

# Animate the gif by creating frames in matplotlib
def update(frame):
    global cum_total
    if frame >= len(all_gdfs):
        return lines_to_draw + list(text_handles.values())
    
    row = all_gdfs.iloc[frame]
    geom_list = explode_multilines(row.geometry)
    
    for geom in geom_list:
        ax.plot(*geom.xy, color='black', linewidth=3, alpha=0.2, zorder=1)  # subtle shadow
        line, = ax.plot(*geom.xy, color=colors.get(row.source_file, 'blue'), linewidth=2.5, zorder=2)
        lines_to_draw.append(line)
    
    # Get month distances for label
    month_total = monthly_distances.get(row.month_idx, 0)

    # get total distance for lable
    cum_total = sum(monthly_distances[i] for i in range(row.month_idx + 1))

    # Update text
    text_handles['month_dist'].set_text(f"Month Distance: {month_total:.1f} km")
    text_handles['cum_dist'].set_text(f"Cumulative: {cum_total:.1f} km")
    
    if row.month_idx < len(month_names):
        text_handles['month'].set_text(f"Month: {month_names[row.month_idx]}")
        text_handles['month_dist'].set_text(f"Month Distance: {month_total:.1f} km")  # <-- use hardcoded value
    text_handles['cum_dist'].set_text(f"Year Distance: {cum_total:.1f} km")

    return lines_to_draw + list(text_handles.values())

# Run the 'gif' i.e. frames, save it and then print a completion message
ani = FuncAnimation(
    fig,
    update,
    frames=len(all_gdfs),
    interval=step_duration * 1000,
    blit=True,
    repeat=False
)

os.makedirs(os.path.dirname(output_file), exist_ok=True)
ani.save(output_file, writer=PillowWriter(fps=int(1/step_duration)))

print(f"Animation saved to {output_file}")

