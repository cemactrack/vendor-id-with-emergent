from typing import Dict, List
from models.vendor import Vendor
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter

class TemplateService:
    
    TEMPLATES = {
        "standard": {
            "name": "Standard Template",
            "colors": {
                "primary": "#16a34a",    # Green
                "secondary": "#0f766e",  # Teal
                "accent": "#eab308"      # Gold
            },
            "features": ["basic_info", "qr_code", "barcode", "photo"]
        },
        "premium": {
            "name": "Premium Template",
            "colors": {
                "primary": "#1e40af",    # Blue
                "secondary": "#7c3aed",  # Purple
                "accent": "#f59e0b"      # Amber
            },
            "features": ["basic_info", "qr_code", "barcode", "photo", "company_info", "security_code"]
        },
        "executive": {
            "name": "Executive Template",
            "colors": {
                "primary": "#991b1b",    # Red
                "secondary": "#92400e",  # Brown
                "accent": "#fbbf24"      # Yellow
            },
            "features": ["basic_info", "qr_code", "barcode", "photo", "company_info", "security_code", "digital_signature", "expiry_date"]
        }
    }
    
    @classmethod
    def get_templates(cls) -> Dict:
        """Get all available templates"""
        return cls.TEMPLATES
    
    @classmethod
    def get_template(cls, template_name: str) -> Dict:
        """Get specific template configuration"""
        return cls.TEMPLATES.get(template_name, cls.TEMPLATES["standard"])
    
    @classmethod
    def validate_template(cls, template_name: str) -> bool:
        """Validate if template exists"""
        return template_name in cls.TEMPLATES
    
    @classmethod
    def get_template_features(cls, template_name: str) -> List[str]:
        """Get features available in a template"""
        template = cls.get_template(template_name)
        return template.get("features", [])
    
    @classmethod
    def generate_enhanced_card_data(cls, vendor: Vendor) -> Dict:
        """Generate enhanced card data based on template"""
        template = cls.get_template(vendor.template)
        features = template["features"]
        
        card_data = {
            "vendor": vendor,
            "template": template,
            "colors": template["colors"],
            "features": {
                "basic_info": "basic_info" in features,
                "company_info": "company_info" in features,
                "security_code": "security_code" in features,
                "digital_signature": "digital_signature" in features,
                "expiry_date": "expiry_date" in features,
                "qr_code": "qr_code" in features,
                "barcode": "barcode" in features,
                "photo": "photo" in features
            }
        }
        
        return card_data
    
    @classmethod
    def create_holographic_pattern(cls, width: int, height: int) -> str:
        """Create a holographic pattern effect"""
        # Create a simple holographic pattern simulation
        img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Create diagonal lines with rainbow colors
        colors = ['#ff0000', '#ff7f00', '#ffff00', '#00ff00', '#0000ff', '#4b0082', '#9400d3']
        line_spacing = 10
        
        for i in range(0, width + height, line_spacing):
            color = colors[i // line_spacing % len(colors)]
            # Convert hex to RGBA with transparency
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            rgba_color = (r, g, b, 30)  # Low opacity for subtle effect
            
            draw.line([(i, 0), (i - height, height)], fill=rgba_color, width=2)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @classmethod
    def create_security_watermark(cls, text: str, width: int, height: int) -> str:
        """Create security watermark"""
        img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position for center
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with low opacity
        draw.text((x, y), text, fill=(128, 128, 128, 50), font=font)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @classmethod
    def create_circuit_pattern(cls, width: int, height: int) -> str:
        """Create enhanced circuit pattern"""
        img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Circuit pattern with nodes and connections
        node_color = (22, 163, 74, 40)  # Green with transparency
        line_color = (22, 163, 74, 30)  # Green with transparency
        
        # Draw circuit nodes
        for x in range(20, width, 40):
            for y in range(20, height, 40):
                draw.ellipse([x-2, y-2, x+2, y+2], fill=node_color)
                
                # Draw connections
                if x + 40 < width:
                    draw.line([x, y, x+40, y], fill=line_color, width=1)
                if y + 40 < height:
                    draw.line([x, y, x, y+40], fill=line_color, width=1)
        
        # Add some random circuit elements
        import random
        for _ in range(10):
            x = random.randint(10, width-10)
            y = random.randint(10, height-10)
            w = random.randint(3, 8)
            h = random.randint(3, 8)
            draw.rectangle([x, y, x+w, y+h], outline=node_color, width=1)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()