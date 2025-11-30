* Python project which overlays .gpx files onto a CartoDB Voyager base map, creating a gif that adds a new route every half a second.
* Also includes a 'card' which shows the monthly distance and counts total distance.

![Screenshot from gif](/Screenshot.png)

__File structure__

```
project/
│
├── build_animation.py       # Main script
├── data/                    # Month folders containing .gpx files in folders with this structure: 01_jan, 02_feb
├── logo.png                 # Branding logo displayed in the animation
└── output/                  # Generated GIF will be saved here
```

__How to run__

1. Ensure data is saved in this format:

```
data/
  01_jan/
    hike.gpx
  02_feb/
    hike.gpx
    ride.gpx
  ...
```

* Note this code assumes there will be hikes and rides (which are then made different colours) - update the code if this is not the case.
* Code will throw an erro rif folders are empty - easiest way to resolve is to remove any empty folders. In this example there is no data for August, so there is no 08_aug folder.

2. Update file paths for:
   * data_folder
   * logo_path
   * output_file

3. Run script


__Customising__
Inside the script you can customise:

* Line colours
* Basemap style
* Logo placement & scale
* The card design
* Hard-coded monthly distances
