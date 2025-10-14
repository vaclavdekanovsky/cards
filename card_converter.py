import json
import csv
from collections import Counter, defaultdict

def process_cards(json_path, csv_path):
    """
    Reads card data from a JSON file, converts it to a CSV file,
    and prints summaries based on transport combinations and continents.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}.")
        return

    if not data:
        print("JSON file is empty.")
        return

    # --- CSV Conversion Setup ---
    headers = data[0].keys()
    rows_for_csv = []

    # --- Summaries Setup ---
    continent_total_counter = Counter()
    transport_combo_counter = Counter()
    continent_transport_counter = defaultdict(Counter)

    # --- Process Data ---
    for card in data:
        # Prepare row for CSV
        row_dict = {}
        for header in headers:
            value = card.get(header, '')
            if isinstance(value, list):
                row_dict[header] = ';'.join(map(str, value))
            else:
                row_dict[header] = value
        rows_for_csv.append(row_dict)

        # --- Update Summaries ---
        continent = card.get('continent')
        transport_list = card.get('transport')

        # Update total continent count
        if continent:
            continent_total_counter[continent] += 1

        # Update combination-based summaries
        if continent and transport_list and isinstance(transport_list, list):
            # Sort the list to treat [bus, train] and [train, bus] as the same combination
            transport_tuple = tuple(sorted(transport_list))
            
            transport_combo_counter[transport_tuple] += 1
            continent_transport_counter[continent][transport_tuple] += 1

    # --- Write the CSV file ---
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows_for_csv)
        print(f"Successfully converted {json_path} to {csv_path}")
    except IOError as e:
        print(f"Error writing to {csv_path}: {e}")

    # --- Print Summaries ---
    print("\n--- Summary by Continent ---")
    if continent_total_counter:
        for continent, count in continent_total_counter.most_common():
            print(f"{continent.capitalize()}: {count}")
    else:
        print("No continent data found.")

    print("\n--- Summary by Transport Combination ---")
    if transport_combo_counter:
        for combo, count in transport_combo_counter.most_common():
            combo_str = ', '.join(combo)
            print(f"[{combo_str}]: {count}")
    else:
        print("No transport data found.")

    print("\n--- Summary by Continent & Transport Combination ---")
    if continent_transport_counter:
        # Sort continents for consistent output
        for continent in sorted(continent_transport_counter.keys()):
            print(f"\nContinent: {continent.capitalize()}")
            # Sort transport combos for this continent by count
            for combo, count in continent_transport_counter[continent].most_common():
                combo_str = ', '.join(combo)
                print(f"  - [{combo_str}]: {count}")
    else:
        print("No transport/continent data found.")


if __name__ == "__main__":
    JSON_FILE = 'cards.json'
    CSV_FILE = 'cards.csv'
    process_cards(JSON_FILE, CSV_FILE)
