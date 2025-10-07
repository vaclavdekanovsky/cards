# Card Generation Project

## Overview

This project is designed to generate travel-themed playing cards. It consists of two main Python scripts:

1.  **`cards.py`**: The primary script that reads card data from a JSON file and generates two types of output:
    *   A single PDF file with all the cards arranged in a grid.
    *   Individual PNG files for each card.
2.  **`continent_downloader.py`**: A utility script to download and create colored PNG images of continents, which can then be used in the card designs.

## Project Structure

```
.
├── cards.py
├── cards.json
├── continent_downloader.py
├── README.md
└── output/
    ├── cards/
    │   ├── mexico_city.png
    │   └── ... (individual card images)
    ├── continents/
    │   ├── africa.png
    │   └── ... (continent images)
    └── cards.pdf
```

## Card Layout

Each card has the following structure:

*   **Main Image**: A large landscape image that forms the background of the top portion of the card.
*   **City Name**: The name of the city or location, displayed prominently at the bottom of the card.
*   **Country Name**: Displayed below the city name.
*   **Flag**: The country's flag, positioned to the right of the city and country names.
*   **Continent Icon**: An outline of the continent, located in the top-right corner of the card.
*   **Transport Icons**: A series of 1 to 3 icons displayed vertically in the right-hand sidebar of the card.
*   **Corner Number**: A number displayed in the bottom-right corner of the card.

## File Descriptions

### `cards.py`

This script is responsible for the main card generation process.

#### `PDFCardGenerator` Class

This class encapsulates all the logic for creating the cards.

*   `__init__(...)`: Initializes the generator with input and output folder paths, and other options like the gap between cards.
*   `generate_pdf(cards_data)`: Creates a single PDF file with all the cards arranged in a grid.
*   `generate_pngs(cards_data)`: Creates individual PNG files for each card and saves them in the `output/cards` directory.
*   `draw_card(c, x, y, card_data)`: The core method that draws a single card onto a given canvas. It handles the positioning of all the elements on the card.
*   `get_image_path(...)`: A helper function to construct the correct path to an image file based on its type (landscape, flag, etc.).
*   `create_rounded_corner_image(...)`: A helper function that takes the main landscape image and applies a rounded corner to it.

### `cards.json`

This file stores the data for each card in a JSON array. Each object in the array represents one card and can contain the following fields:

*   `image`: The filename of the main landscape image.
*   `city`: The name of the city/location.
*   `country`: The name of the country.
*   `flag`: The filename of the country's flag image.
*   `continent`: The filename of the continent outline image.
*   `transport`: A list of strings representing the transport icons to be displayed (e.g., `["bus", "train"]`).
*   `corner_number`: The number to be displayed in the bottom-right corner.
*   `corner_font_size`: The font size for the corner number.

### `continent_downloader.py`

This is a utility script to generate the continent outline images used on the cards. It downloads an SVG world map, isolates each continent, applies a specified color, and saves it as a PNG file with a white background into the `output/continents` folder.

## How to Use

1.  **Prepare Images**: Place your image files in the appropriate subfolders within your main input folder (e.g., `C:\Vasa\Cartoon\Travel Game\in`).
    *   `landscapes/`
    *   `flags/`
    *   `transport_icons/`
    *   `continents/`

2.  **Generate Continent Images (Optional)**: If you need to generate the continent images, run the `continent_downloader.py` script. This will create the `output/continents` directory and populate it with the PNG images.

3.  **Generate Cards**: Run the `cards.py` script. This will generate:
    *   The main PDF file (`cards.pdf`) in the `output` folder.
    *   Individual PNG files for each card in the `output/cards` subfolder.

## Dependencies

This project requires the following Python libraries:

*   `reportlab`: For PDF generation.
*   `Pillow`: For image manipulation.
*   `pdf2image`: For converting the individual card PDFs to PNGs.

Note that `pdf2image` has an external dependency on **Poppler**. You will need to have Poppler installed on your system for the PNG generation to work.