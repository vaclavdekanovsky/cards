from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
import tempfile
import json
import io
import os

class PDFCardGenerator:
    def __init__(self, input_folder="input", output_folder="output", output_filename="cards.pdf", gap=1 * mm):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.gap = gap
        
        # Create folders if they don't exist
        os.makedirs(input_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        
        self.output_filename = os.path.join(output_folder, output_filename)
        self.cards_output_dir = os.path.join(self.output_folder, "cards")
        os.makedirs(self.cards_output_dir, exist_ok=True)
        
        # Register Gagalin font (if available)
        try:
            # Try to register Gagalin font from input folder (TTF or OTF)
            gagalin_ttf = os.path.join(input_folder, "Gagalin Regular.ttf")
            gagalin_otf = os.path.join(input_folder, "Gagalin-Regular.otf")
            
            if os.path.exists(gagalin_ttf):
                pdfmetrics.registerFont(TTFont('Gagalin', gagalin_ttf))
                self.font_name = 'Gagalin'
                print("Using Gagalin font (TTF)")
            elif os.path.exists(gagalin_otf):
                pdfmetrics.registerFont(TTFont('Gagalin', gagalin_otf))
                self.font_name = 'Gagalin'
                print("Using Gagalin font (OTF)")
            else:
                print("Gagalin font not found. Please download Gagalin-Regular.ttf or .otf to input folder.")
                print("Using Helvetica-Bold as fallback")
                self.font_name = 'Helvetica-Bold'
        except Exception as e:
            print(f"Error loading font: {e}")
            self.font_name = 'Helvetica-Bold'
        
        # A4 landscape dimensions
        self.page_width, self.page_height = landscape(A4)
        
        # Card specifications
        self.card_width = 9.57 * cm
        self.card_height = 6.67 * cm
        self.border_width = 2
        self.corner_radius = 10 * mm
        
        # Image area (3:2 ratio)
        self.img_width = 8.25 * cm
        self.img_height = 5.5 * cm
        
        # Grid layout
        self.cards_per_row = 3
        self.cards_per_col = 3
        self.cards_per_page = 9
    
    def get_image_path(self, filename, image_type):
        """Get full path for image from input folder"""
        if os.path.isabs(filename):
            return filename
        return os.path.join(self.input_folder, image_type, filename)
    
    def create_rounded_corner_image(self, img_path, image_type):
        """Create image with rounded top-left corner - IMPROVED QUALITY VERSION"""
        full_path = self.get_image_path(img_path, image_type)
        img = Image.open(full_path)
        
        # Convert to RGB if necessary (handles RGBA, P mode, etc.)
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        # Calculate target dimensions in pixels at higher DPI for better quality
        # Use 300 DPI instead of 72 DPI for much better quality
        dpi_multiplier = 300 / 72  # ~4.17x resolution
        target_width = int(self.img_width * dpi_multiplier)
        target_height = int(self.img_height * dpi_multiplier)
        
        # Resize with high-quality resampling
        # LANCZOS is best for downscaling
        img = img.resize((target_width, target_height), Image.LANCZOS)
        
        # Convert to RGBA for transparency
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create mask for rounded corner at higher resolution
        mask = Image.new('L', img.size, 255)
        draw = ImageDraw.Draw(mask)
        
        # Draw rounded rectangle (only top-left corner rounded)
        # Scale corner radius to match higher resolution
        radius = int(self.corner_radius * dpi_multiplier)
        
        # Black out top-left corner
        draw.rectangle([0, 0, radius, radius], fill=0)
        # Draw white circle for rounded effect
        draw.ellipse([0, 0, radius * 2, radius * 2], fill=255)
        
        # Apply mask
        img.putalpha(mask)
        
        return img
    
    def draw_card_border(self, c, x, y):
        """Draw card border with rounded corners"""
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(self.border_width)
        c.roundRect(x, y, self.card_width, self.card_height, 
                    self.corner_radius, stroke=1, fill=0)
    
    def draw_image_border(self, c, x, y):
        """Draw border for image area - extends to bottom of card"""
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(self.border_width)
        
        # Draw right border - extends from top of image to bottom of card
        c.line(x + self.img_width, y - (self.card_height - self.img_height), 
               x + self.img_width, y + self.img_height)
        # Draw bottom border - extends full width to edge
        c.line(x, y, x + self.card_width, y)
    
    def draw_card(self, c, x, y, card_data):
        """Draw a single card at position (x, y)"""
        # Draw main image with rounded corner FIRST
        if 'image' in card_data:
            try:
                img = self.create_rounded_corner_image(card_data['image'], 'landscapes')
                img_buffer = io.BytesIO()
                
                # Save as PNG with NO compression for maximum quality
                img.save(img_buffer, format='PNG', compress_level=0)
                img_buffer.seek(0)
                img_reader = ImageReader(img_buffer)
                
                # Draw at the physical size - reportlab will handle the high-res image
                c.drawImage(img_reader, x, y + self.card_height - self.img_height, 
                          width=self.img_width, height=self.img_height, 
                          mask='auto', preserveAspectRatio=True)
            except Exception as e:
                print(f"Error loading image {card_data['image']}: {e}")
        
        # --- Text and Flag Section ---

        # Define layout parameters
        flag_size = 1 * cm
        gap = 0.2 * cm
        
        # Get city text and font size
        city_text = card_data.get('city', 'City')
        city_font_size = 16
        c.setFont(self.font_name, city_font_size)
        
        # Calculate initial text width
        city_text_width = c.stringWidth(city_text, self.font_name, city_font_size)

        # --- Dynamic Positioning and Font Sizing ---

        # Define available width under the image
        text_area_width = self.img_width
        
        # Check if the text is "long" (e.g., > 70% of the available area width)
        is_long_text = (flag_size + gap + city_text_width) > (text_area_width * 0.7)

        if is_long_text:
            # For long text, align to the left with a small margin
            left_margin = 0.5 * cm # Increased from 0.2cm
            right_margin = 0.2 * cm
        else:
            # For shorter text, center it more
            left_margin = 1.2 * cm
            right_margin = 0.2 * cm

        # Available width for text, flag, and gap
        available_width = text_area_width - left_margin - right_margin
        
        # Total content width
        total_content_width = flag_size + gap + city_text_width
        
        # Reduce font size until it fits
        while total_content_width > available_width and city_font_size > 8:
            city_font_size -= 1
            c.setFont(self.font_name, city_font_size)
            city_text_width = c.stringWidth(city_text, self.font_name, city_font_size)
            total_content_width = flag_size + gap + city_text_width

        # Set final positions
        flag_x = x + left_margin
        text_x = flag_x + flag_size + gap

        # --- Drawing ---

        # Draw flag on the left
        if 'flag' in card_data:
            try:
                flag_y = y + 0.25 * cm
                flag_path = self.get_image_path(card_data['flag'], 'flags')
                c.drawImage(flag_path, flag_x, flag_y,
                          width=flag_size, height=flag_size * 0.67, preserveAspectRatio=True)
            except Exception as e:
                print(f"Error loading flag {card_data['flag']}: {e}")

        # Draw city name with adjusted font size
        c.setFont(self.font_name, city_font_size)
        text_y = y + 0.55 * cm
        c.drawString(text_x, text_y, city_text)
        
        # Draw country name
        c.setFont(self.font_name, 10)
        country_text = card_data.get('country', 'Country')
        c.drawString(text_x, text_y - 0.4 * cm, country_text)
        
        # Draw continent outline (top right)
        if 'continent' in card_data:
            try:
                continent_size = 1.3 * cm
                continent_x = x + self.card_width - continent_size - 0.1 * cm
                continent_y = y + self.card_height - continent_size - 0.2 * cm
                continent_image = f"{card_data['continent']}_outline.png"
                continent_path = self.get_image_path(continent_image, 'continents')
                c.drawImage(continent_path, continent_x, continent_y,
                          width=continent_size, height=continent_size, preserveAspectRatio=True)
            except Exception as e:
                print(f"Error loading continent {card_data['continent']}: {e}")
        
        # Draw transport icons (right side, middle)
        if 'transport' in card_data and isinstance(card_data['transport'], list):
            try:
                icon_size = 1.0 * cm
                transport_icons = card_data['transport']
                transport_count = len(transport_icons)
                
                # Center horizontally in the right sidebar
                sidebar_width = self.card_width - self.img_width
                icon_x = x + self.img_width + (sidebar_width - icon_size) / 2

                # Center vertically in the right sidebar
                icon_spacing = 0.1 * cm
                total_icon_height = transport_count * icon_size + (transport_count - 1) * icon_spacing
                sidebar_y_start = y + self.card_height - self.img_height
                icon_start_y = sidebar_y_start + (self.img_height - total_icon_height) / 2 + total_icon_height - icon_size - 0.5 * cm

                for i, icon_name in enumerate(transport_icons):
                    icon_y = icon_start_y - (i * (icon_size + icon_spacing))
                    transport_path = self.get_image_path(f"{icon_name}.png", 'transport_icons')
                    c.saveState()
                    c.translate(icon_x + icon_size / 2, icon_y + icon_size / 2)
                    c.rotate(90)
                    c.drawImage(transport_path, -icon_size / 2, -icon_size / 2,
                                  width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
                    c.restoreState()
            except Exception as e:
                print(f"Error loading transport icon: {e}")
        
        # Draw corner number
        corner_number = card_data.get('corner_number', '1')
        corner_font_size = card_data.get('corner_font_size', 16)
        c.setFont(self.font_name, corner_font_size)
        
        corner_area_x = x + self.img_width + (self.card_width - self.img_width) / 2
        corner_area_y = y + (self.card_height - self.img_height) / 2 - (corner_font_size / 4) # Adjust for better vertical centering
        c.drawCentredString(corner_area_x, corner_area_y, str(corner_number))

        # Draw borders LAST so they appear on top
        self.draw_card_border(c, x, y)
        self.draw_image_border(c, x, y + self.card_height - self.img_height)

    def generate_pngs(self, cards_data):
        print("Generating individual card PNGs...")
        for card_data in cards_data:
            with tempfile.TemporaryDirectory() as temp_dir:
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=(self.card_width, self.card_height))
                self.draw_card(c, 0, 0, card_data)
                c.save()

                images = convert_from_bytes(buffer.getvalue(), output_folder=temp_dir, fmt='png', single_file=True)
                
                if 'image' in card_data:
                    image_name = os.path.splitext(card_data['image'])[0]
                    output_path = os.path.join(self.cards_output_dir, f"{image_name}.png")
                    
                    if images:
                        images[0].save(output_path, 'PNG')
                        print(f"Saved {output_path}")

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
            
            # Start new page after 9 cards
            if card_count % self.cards_per_page == 0 and card_count < len(cards_data):
                c.showPage()
        
        c.save()
        print(f"PDF generated: {self.output_filename}")

def main():
    # Load configuration from JSON file
    config_path = os.path.join(os.path.dirname(__file__), "configuration.json")
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Create generator with custom folders
    generator = PDFCardGenerator(
        input_folder=config['input_folder'],
        output_folder=config['output_folder'],
        output_filename="cards.pdf",
        gap=1
    )
    
    # Load from JSON file in the script's directory
    json_path = os.path.join(os.path.dirname(__file__), "cards.json")
    with open(json_path, 'r') as f:
        cards_data = json.load(f)
    generator.generate_pdf(cards_data)
    generator.generate_pngs(cards_data)

if __name__ == "__main__":
    main()