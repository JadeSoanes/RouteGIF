* Python project which overlays .gpx files onto a base map, creating a gif that adds a new route every half a second.
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

