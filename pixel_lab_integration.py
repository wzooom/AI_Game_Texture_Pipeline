import os
import json
import random
from io import BytesIO

# Import texture_generator constants for consistency
from texture_generator import IMAGE_LIBS_AVAILABLE

# Try to import optional dependencies with fallbacks
if IMAGE_LIBS_AVAILABLE:
    import requests
    from PIL import Image

class PixelLabIntegration:
    def __init__(self, api_key=None):
        """Initialize the Pixel Lab integration with API key"""
        # Try to get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get("PIXEL_LAB_API_KEY")
        if not self.api_key:
            print("Warning: No Pixel Lab API key provided. Please set PIXEL_LAB_API_KEY environment variable.")
        
        # Create directories for storing textures if they don't exist
        self.texture_dir = os.path.join(os.path.dirname(__file__), "assets", "textures")
        os.makedirs(self.texture_dir, exist_ok=True)
    
    def generate_texture_image(self, prompt, texture_type, level_num, size=(256, 256)):
        """Generate a texture image using Pixel Lab API"""
        if not self.api_key:
            # Return a placeholder image if no API key is available
            return self._generate_placeholder_image(texture_type, level_num, size)
        
        try:
            # In a real implementation, this would call the Pixel Lab API
            # For now, we'll simulate the API call
            print(f"Simulating Pixel Lab API call for {texture_type} in level {level_num}")
            print(f"Prompt: {prompt}")
            
            # This is where you would make the actual API call to Pixel Lab
            # response = requests.post(
            #     "https://api.pixellab.ai/generate",
            #     headers={"Authorization": f"Bearer {self.api_key}"},
            #     json={"prompt": prompt, "width": size[0], "height": size[1]}
            # )
            # image_data = response.json().get("image")
            # image = Image.open(BytesIO(base64.b64decode(image_data)))
            
            # For now, generate a placeholder image
            image = self._generate_placeholder_image(texture_type, level_num, size)
            
            # Save the image
            filename = self._get_texture_filename(texture_type, level_num)
            image.save(filename)
            print(f"Saved texture to {filename}")
            
            return image, filename
            
        except Exception as e:
            print(f"Error generating texture with Pixel Lab: {e}")
            return self._generate_placeholder_image(texture_type, level_num, size)
    
    def _generate_placeholder_image(self, texture_type, level_num, size=(256, 256)):
        """Generate a placeholder image for testing"""
        # Check if PIL is available
        if not IMAGE_LIBS_AVAILABLE:
            print(f"Cannot generate placeholder image for {texture_type} - PIL not available")
            # Return filename only since we can't generate an image
            filename = self._get_texture_filename(texture_type, level_num)
            return None, filename
            
        # Create a base image
        image = Image.new('RGB', size)
        pixels = image.load()
        
        # Set base colors based on texture type and level
        if texture_type == "background":
            # Background colors by level
            if level_num == 1:
                base_color = (25, 75, 180)  # Blue sky theme
            elif level_num == 2:
                base_color = (70, 40, 120)  # Purple twilight theme
            else:
                base_color = (20, 20, 50)   # Dark night theme
        elif texture_type == "platform":
            # Platform colors by level
            if level_num == 1:
                base_color = (120, 80, 40)  # Brown wood
            elif level_num == 2:
                base_color = (100, 100, 120)  # Stone
            else:
                base_color = (80, 40, 40)  # Dark brick
        elif texture_type == "enemy":
            # Enemy colors by level
            if level_num == 1:
                base_color = (180, 60, 60)  # Red
            elif level_num == 2:
                base_color = (60, 160, 60)  # Green
            else:
                base_color = (60, 60, 180)  # Blue
        elif texture_type == "boss":
            # Boss is special - make it stand out
            base_color = (200, 50, 200)  # Bright purple
        else:
            # Default gray
            base_color = (128, 128, 128)
        
        # Create a more interesting pattern based on texture type
        for x in range(size[0]):
            for y in range(size[1]):
                # Add some noise and patterns
                noise = random.randint(-20, 20)
                
                if texture_type == "background":
                    # Add gradient for background
                    gradient = int(y / size[1] * 50)
                    r = max(0, min(255, base_color[0] + noise - gradient))
                    g = max(0, min(255, base_color[1] + noise))
                    b = max(0, min(255, base_color[2] + noise + gradient))
                    
                elif texture_type == "platform":
                    # Add grid pattern for platforms
                    grid = (x % 16 < 2 or y % 16 < 2) * 20
                    r = max(0, min(255, base_color[0] + noise - grid))
                    g = max(0, min(255, base_color[1] + noise - grid))
                    b = max(0, min(255, base_color[2] + noise - grid))
                    
                elif texture_type == "enemy":
                    # Add circular pattern for enemies
                    center_x, center_y = size[0] // 2, size[1] // 2
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    circle = int(abs(dist % 20 - 10) * 5)
                    r = max(0, min(255, base_color[0] + noise - circle))
                    g = max(0, min(255, base_color[1] + noise - circle))
                    b = max(0, min(255, base_color[2] + noise - circle))
                    
                elif texture_type == "boss":
                    # Add radial pattern for boss
                    center_x, center_y = size[0] // 2, size[1] // 2
                    angle = (abs(x - center_x) + abs(y - center_y)) % 30
                    radial = int(angle * 3)
                    r = max(0, min(255, base_color[0] + noise + radial))
                    g = max(0, min(255, base_color[1] + noise - radial))
                    b = max(0, min(255, base_color[2] + noise + radial))
                    
                else:
                    # Default pattern
                    r = max(0, min(255, base_color[0] + noise))
                    g = max(0, min(255, base_color[1] + noise))
                    b = max(0, min(255, base_color[2] + noise))
                
                pixels[x, y] = (r, g, b)
        
        # Save the image and return both image and filename
        filename = self._get_texture_filename(texture_type, level_num)
        try:
            image.save(filename)
            print(f"Saved placeholder texture to {filename}")
        except Exception as e:
            print(f"Error saving placeholder image: {e}")
            
        return image, filename
    
    def _get_texture_filename(self, texture_type, level_num):
        """Get the filename for a texture"""
        return os.path.join(self.texture_dir, f"level_{level_num}_{texture_type}.png")
    
    def generate_all_textures_from_descriptions(self, level_descriptions):
        """Generate all textures from descriptions"""
        texture_files = {}
        
        for level_num, descriptions in level_descriptions.items():
            texture_files[level_num] = {}
            
            for texture_type, description in descriptions.items():
                # Generate a Pixel Lab prompt from the description
                prompt = f"pixel art, 16-bit style, game asset, {description}"
                
                # Generate the texture image
                _, filename = self.generate_texture_image(prompt, texture_type, level_num)
                
                # Store the filename
                texture_files[level_num][texture_type] = filename
        
        return texture_files


# Example usage
if __name__ == "__main__":
    # Load texture descriptions from file
    texture_dir = os.path.join(os.path.dirname(__file__), "assets", "textures")
    level_descriptions = {}
    
    for level_num in range(1, 4):
        filename = os.path.join(texture_dir, f"level_{level_num}_descriptions.json")
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                level_descriptions[level_num] = json.load(f)
    
    # Initialize Pixel Lab integration
    pixel_lab = PixelLabIntegration()
    
    # Generate textures
    texture_files = pixel_lab.generate_all_textures_from_descriptions(level_descriptions)
    
    # Print the texture files
    for level_num, textures in texture_files.items():
        print(f"\nLevel {level_num} Texture Files:")
        for texture_type, filename in textures.items():
            print(f"  {texture_type.capitalize()}: {filename}")
