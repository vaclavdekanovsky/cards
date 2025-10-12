from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from PIL import Image
import os
import json
import io

class PDFTransportCardGenerator:
    def __init__(self, input_folder="in", output_folder="output", output_filename="transport_cards.pdf", gap=0, corner_radius=3 * mm):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.gap = gap
        self.corner_radius = corner_radius
        
        # Create folders if they don't exist
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
        self.output_filename = os.path.join(self.output_folder, output_filename)
        
        # A4 landscape dimensions
        self.page_width, self.page_height = landscape(A4)
        
        # Grid layout
        self.cards_per_row = 5
        self.cards_per_col = 4
        self.cards_per_page = 20

        # Card specifications for a 5x4 grid with margin
        self.margin = 0.5 * cm
        usable_width = self.page_width - 2 * self.margin
        usable_height = self.page_height - 2 * self.margin
        self.card_width = (usable_width - (self.cards_per_row - 1) * self.gap) / self.cards_per_row
        self.card_height = (usable_height - (self.cards_per_col - 1) * self.gap) / self.cards_per_col
    
    def get_image_path(self, filename, image_type):
        """Get full path for image from input folder"""
        return os.path.join(self.input_folder, image_type, filename)
    
    def draw_card(self, c, x, y, card_data):
        """Draw a single card at position (x, y)"""
        # Draw main image
        if 'image' in card_data:
            try:
                img_path = self.get_image_path(card_data['image'], 'transport_icons')
                img = Image.open(img_path)
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                img_reader = ImageReader(img_buffer)
                
                # Center image in the card
                img_width, img_height = self.card_width * 0.8, self.card_height * 0.8
                img_x = x + (self.card_width - img_width) / 2
                img_y = y + (self.card_height - img_height) / 2

                c.drawImage(img_reader, img_x, img_y, 
                          width=img_width, height=img_height, 
                          mask='auto', preserveAspectRatio=True)
            except Exception as e:
                print(f"Error loading image {card_data['image']}: {e}")
        
        # Draw card border
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.roundRect(x, y, self.card_width, self.card_height, self.corner_radius, stroke=1, fill=0)

    def generate_pdf(self, cards_data):
        """Generate PDF from cards data"""
        c = canvas.Canvas(self.output_filename, pagesize=landscape(A4))
        
        gap = self.gap

        # Calculate margins to center the grid
        total_width = self.cards_per_row * self.card_width + (self.cards_per_row - 1) * gap
        total_height = self.cards_per_col * self.card_height + (self.cards_per_col - 1) * gap
        margin_x = (self.page_width - total_width) / 2
        margin_y = (self.page_height - total_height) / 2
        
        card_count = 0
        for card_data in cards_data:
            # Calculate position in grid
            page_card_idx = card_count % self.cards_per_page
            row = page_card_idx // self.cards_per_row
            col = page_card_idx % self.cards_per_row
            
            # Calculate card position (from bottom-left)
            x = margin_x + col * (self.card_width + gap)
            y = margin_y + (self.cards_per_col - 1 - row) * (self.card_height + gap)
            
            # Draw the card
            self.draw_card(c, x, y, card_data)
            
            card_count += 1
            
            # Start new page if needed
            if card_count % self.cards_per_page == 0 and card_count < len(cards_data):
                c.showPage()
        
        c.save()
        print(f"PDF generated: {self.output_filename}")

def get_transport_icons_data(input_folder):
    transport_icons_path = os.path.join(input_folder, 'transport_icons')
    if not os.path.exists(transport_icons_path):
        print(f"Error: Directory not found at '{transport_icons_path}'")
        print("Please create the directory and add your transport icon images.")
        return []

    transport_counts = {
        "bus": 20,
        "train": 15,
        "boat": 13,
        "plane": 12
    }
    
    cards_data = []
    for transport_type, count in transport_counts.items():
        image_name = f"{transport_type}.png"
        image_path = os.path.join(transport_icons_path, image_name)
        if os.path.exists(image_path):
            for _ in range(count):
                cards_data.append({"image": image_name})
        else:
            print(f"Warning: Image not found - {image_path}")
    
    return cards_data

def main():
    # Load configuration from JSON file
    config_path = os.path.join(os.path.dirname(__file__), "configuration.json")
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Create generator with custom folders
    generator = PDFTransportCardGenerator(
        input_folder=config['input_folder'],
        output_folder=config['output_folder'],
        output_filename="transport_cards.pdf",
        gap=1
    )
    
    cards_data = get_transport_icons_data(generator.input_folder)
    
    if cards_data:
        generator.generate_pdf(cards_data)

if __name__ == "__main__":
    main()
