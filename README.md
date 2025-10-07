# Project Overview

This project contains two main Python scripts:

1.  `cards.py`: A script to generate a PDF file of cards based on data from a JSON file.
2.  `continent_downloader.py`: A script to generate PNG images of continents with specified colors.

## Project Structure

```
.
├── cards.py
├── cards.json
├── continent_downloader.py
└── output/
    ├── africa.png
    ├── antarctica.png
    ├── asia.png
    ├── europe.png
    ├── north-america.png
    ├── oceania.png
    └── south-america.png
```

### `cards.py`

This script uses the `reportlab` library to create a PDF file containing cards. The data for the cards is read from the `cards.json` file. The script is configured to arrange the cards in a 3x3 grid on each page.

### `cards.json`

This file contains the data for the cards in JSON format. Each object in the array represents a card and contains properties like the city name, country, and image file names.

### `continent_downloader.py`

This script generates PNG images of continents. It uses an embedded SVG world map with identified continents. The script extracts each continent, applies a color from a predefined dictionary, and saves it as a separate PNG file with a white background in the `output` directory.

## How to Use

1.  **Generate Continent Images:**
    - Run the `continent_downloader.py` script. This will create the `output` directory and populate it with PNG images of the continents.

2.  **Generate the Card PDF:**
    - Ensure that the image files referenced in `cards.json` are present in the specified input folder (as configured in `cards.py`).
    - Run the `cards.py` script to generate the `cards.pdf` file.
