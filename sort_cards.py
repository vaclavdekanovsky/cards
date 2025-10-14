import json

# Define the custom sort order for transport combinations.
# Sorting the lists here ensures that combos like ['bus', 'train'] and ['train', 'bus'] are treated the same.
TRANSPORT_ORDER_MAP = {
    tuple(sorted(['bus', 'bus'])): 0,
    tuple(sorted(['bus', 'train'])): 1,
    tuple(sorted(['bus', 'boat'])): 2,
    tuple(sorted(['train', 'boat'])): 3,
    tuple(sorted(['bus', 'train', 'boat'])): 4,
}

def get_transport_sort_key(transport_list):
    """Helper function to get the sort key for a card's transport list."""
    if not transport_list or not isinstance(transport_list, list):
        return 99  # Sort items without transport last

    # Normalize the transport list by sorting it and converting to a tuple
    transport_tuple = tuple(sorted(transport_list))

    # Return the predefined order, or a default value for any other combinations
    return TRANSPORT_ORDER_MAP.get(transport_tuple, 99)

def sort_cards_data(data):
    """Sorts the card data based on continent and the custom transport order."""
    # Use a lambda function to create a sort key: (continent, transport_order)
    # This sorts by continent first, then by the transport key.
    return sorted(data, key=lambda card: (
        card.get('continent', ''),
        get_transport_sort_key(card.get('transport'))
    ))

def main():
    """Main function to read, sort, and overwrite the JSON file."""
    json_path = 'cards.json'

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            cards_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}.")
        return

    print("Sorting card data...")
    sorted_data = sort_cards_data(cards_data)

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            # Use indent=4 for pretty-printing the JSON output
            json.dump(sorted_data, f, indent=4)
        print(f"Successfully sorted and updated {json_path}.")
    except IOError as e:
        print(f"Error writing to {json_path}: {e}")


if __name__ == "__main__":
    main()
