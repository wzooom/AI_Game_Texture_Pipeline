"""
Consolidated AI Texture Generation Pipeline

This module combines all AI-related functionality into a single, maintainable class:
- OpenAI API integration for texture descriptions
- PixelLab API integration for image generation
- Prompt management and customization
- Fallback systems and error handling
- Texture saving and verification
"""

import os
import json
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Try to import OpenAI with fallback
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print("Warning: OpenAI package not available. Using fallback texture descriptions.")
    OPENAI_AVAILABLE = False

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AITexturePipeline:
    """
    Unified AI texture generation pipeline that handles:
    - OpenAI text generation for descriptions
    - PixelLab image generation 
    - Prompt management and themes
    - Fallback systems
    - File management
    """
    
    def __init__(self, openai_key=None, pixellab_key=None):
        """Initialize the AI pipeline with API keys"""
        # API keys
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY")
        self.pixellab_key = pixellab_key or os.environ.get("PIXEL_LAB_API_KEY")
        
        # Initialize OpenAI
        self._setup_openai()
        
        # Setup directories
        self.base_dir = os.path.dirname(__file__)
        self.texture_dir = os.path.join(self.base_dir, "assets", "textures")
        self.verification_dir = os.path.join(self.base_dir, "assets", "pixellab_generated")
        os.makedirs(self.texture_dir, exist_ok=True)
        os.makedirs(self.verification_dir, exist_ok=True)
        
        # Load prompt configuration
        self.prompt_config = self._load_prompt_config()
        self.current_theme = "desert ruins"  # Default theme
        
        # Cache for generated descriptions
        self.description_cache = {}
        
        # Texture types
        self.texture_types = ["background", "platform", "enemy", "boss"]
        
        print("🚀 AI Texture Pipeline initialized successfully")
    
    def _setup_openai(self):
        """Setup OpenAI API with proper version handling"""
        if not self.openai_key or not OPENAI_AVAILABLE:
            print("⚠️ OpenAI API key not available - using fallback descriptions")
            return
        
        # For OpenAI v0.28.1, use the old API format
        openai.api_key = self.openai_key
        print("✅ OpenAI API (v0.28.1) initialized successfully")
    
    def _load_prompt_config(self):
        """Load prompt configuration from JSON file"""
        config_path = os.path.join(self.base_dir, "prompt_config.json")
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration if file not found
            return self._get_default_prompt_config()
    
    def _get_default_prompt_config(self):
        """Return default prompt configuration"""
        return {
            "themes": {
                "desert ruins": {
                    "name": "Desert Ruins",
                    "description": "Ancient desert ruins with sandstone architecture",
                    "prompts": {
                        "background": "A vast desert landscape with ancient ruins, sandstone pillars, and warm golden lighting",
                        "platform": "A sturdy sandstone platform with desert ruins elements, weathered texture",
                        "enemy": "A desert creature or ancient guardian with sandy, ruined aesthetic",
                        "boss": "An imposing desert boss with ancient ruins elements, large and threatening"
                    }
                },
                "sci-fi futuristic": {
                    "name": "Sci-Fi Futuristic",
                    "description": "High-tech futuristic world with neon lights and cyberpunk elements",
                    "prompts": {
                        "background": "A high-tech futuristic world with neon lights and cyberpunk elements",
                        "platform": "A sturdy high-tech platform with futuristic elements and neon accents",
                        "enemy": "A futuristic robot or cyber creature with neon and tech elements",
                        "boss": "An imposing final boss with high-tech futuristic elements, large and threatening"
                    }
                }
            }
        }
    
    def generate_all_textures(self, num_levels=3):
        """
        Generate all textures for all levels
        Returns: dict of texture files organized by level
        """
        print(f"🎨 Generating textures with theme: {self.current_theme}")
        
        texture_files = {}
        
        for level_num in range(1, num_levels + 1):
            print(f"\n📁 Generating Level {level_num} textures...")
            texture_files[level_num] = {}
            
            # Generate descriptions first
            descriptions = self._generate_level_descriptions(level_num)
            
            # Generate images for each texture type
            for texture_type in self.texture_types:
                # Skip boss texture for non-final levels
                if texture_type == "boss" and level_num != num_levels:
                    continue
                
                description = descriptions.get(texture_type, f"Default {texture_type}")
                prompt = self._create_image_prompt(description, texture_type)
                
                # Generate the texture image
                image, filename = self._generate_texture_image(prompt, texture_type, level_num)
                texture_files[level_num][texture_type] = filename
            
            # Save descriptions to file
            self._save_descriptions(descriptions, level_num)
        
        print("\n✅ Generated textures for all levels")
        return texture_files
    
    def _generate_level_descriptions(self, level_num):
        """Generate AI descriptions for all textures in a level"""
        cache_key = f"{self.current_theme}_{level_num}"
        
        if cache_key in self.description_cache:
            return self.description_cache[cache_key]
        
        descriptions = {}
        is_final_level = (level_num == 3)  # Assuming 3 levels
        
        for texture_type in self.texture_types:
            # Skip boss for non-final levels
            if texture_type == "boss" and not is_final_level:
                continue
            
            # Generate description using OpenAI or fallback
            description = self._generate_ai_description(texture_type, level_num, is_final_level)
            descriptions[texture_type] = description
        
        # Cache the descriptions
        self.description_cache[cache_key] = descriptions
        return descriptions
    
    def _generate_ai_description(self, texture_type, level_num, is_final_level):
        """Generate AI description using OpenAI API or fallback"""
        if not self.openai_key or not OPENAI_AVAILABLE:
            return self._get_fallback_description(texture_type, level_num)
        
        try:
            # Create prompt for OpenAI
            prompt = self._create_description_prompt(texture_type, level_num, is_final_level)
            
            # Use OpenAI v0.28.1 API format
            if hasattr(openai, 'ChatCompletion'):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a game asset designer specializing in pixel art descriptions."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                description = response.choices[0].message.content.strip()
                print(f"✅ Generated AI description for {texture_type} (level {level_num})")
                return description
            else:
                # Fallback to Completion API
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=f"You are a game asset designer specializing in pixel art descriptions.\n\n{prompt}",
                    max_tokens=150,
                    temperature=0.7
                )
                description = response.choices[0].text.strip()
                print(f"✅ Generated AI description for {texture_type} (level {level_num})")
                return description
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._get_fallback_description(texture_type, level_num)
    
    def _create_description_prompt(self, texture_type, level_num, is_final_level):
        """Create prompt for OpenAI description generation"""
        theme_data = self.prompt_config["themes"].get(self.current_theme, {})
        theme_desc = theme_data.get("description", "generic game environment")
        
        base_prompt = f"Create a detailed description for a {texture_type} texture in a {theme_desc} themed level {level_num} of a 2D platformer game."
        
        if texture_type == "background":
            return f"{base_prompt} The background should set the mood and atmosphere for the level."
        elif texture_type == "platform":
            return f"{base_prompt} The platform should be sturdy and fit the theme, suitable for jumping."
        elif texture_type == "enemy":
            return f"{base_prompt} The enemy should be challenging but not overwhelming, fitting the theme."
        elif texture_type == "boss" and is_final_level:
            return f"{base_prompt} This is the final boss - make it imposing, large, and thematically appropriate."
        
        return base_prompt
    
    def _get_fallback_description(self, texture_type, level_num):
        """Get fallback description when AI is not available"""
        theme_data = self.prompt_config["themes"].get(self.current_theme, {})
        prompts = theme_data.get("prompts", {})
        
        return prompts.get(texture_type, f"A {texture_type} for level {level_num}")
    
    def _create_image_prompt(self, description, texture_type):
        """Create detailed prompt for image generation"""
        base_style = "pixel art, 16-bit style, game asset"
        quality_terms = "high quality, detailed, crisp, vibrant colors, good contrast, clean pixel art, no blur, sharp edges, optimized for game sprites"
        
        return f"{base_style}, {description}, {quality_terms}"
    
    def _generate_texture_image(self, prompt, texture_type, level_num, size=(256, 256)):
        """Generate texture image using PixelLab API or fallback"""
        if not self.pixellab_key:
            print(f"No PixelLab API key - using placeholder for {texture_type} level {level_num}")
            return self._generate_placeholder_image(texture_type, level_num, size)
        
        try:
            print(f"🎨 Calling PixelLab API for {texture_type} in level {level_num}")
            print(f"📝 Prompt: {prompt}")
            
            # Make the actual API call to PixelLab
            response = requests.post(
                "https://api.pixellab.ai/v1/generate",
                headers={
                    "Authorization": f"Bearer {self.pixellab_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "width": size[0],
                    "height": size[1],
                    "style": "pixel-art",
                    "quality": "high"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if "image" in result:
                    import base64
                    image_data = base64.b64decode(result["image"])
                    image = Image.open(BytesIO(image_data))
                elif "url" in result:
                    img_response = requests.get(result["url"], timeout=30)
                    image = Image.open(BytesIO(img_response.content))
                else:
                    raise ValueError("Unexpected API response format")
                
                # Save the real AI-generated image
                filename = self._save_texture_image(image, texture_type, level_num)
                print(f"✅ Generated real AI texture: {filename}")
                
                return image, filename
                
            else:
                print(f"❌ PixelLab API error {response.status_code}: {response.text}")
                print(f"🔄 Falling back to placeholder generation")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ PixelLab API request failed: {e}")
            print(f"🔄 Falling back to placeholder generation")
        except Exception as e:
            print(f"❌ PixelLab API error: {e}")
            print(f"🔄 Falling back to placeholder generation")
        
        # Fallback to placeholder
        print(f"🎨 Generating placeholder for {texture_type} level {level_num}")
        return self._generate_placeholder_image(texture_type, level_num, size)
    
    def _generate_placeholder_image(self, texture_type, level_num, size=(256, 256)):
        """Generate a placeholder image for testing"""
        # Create a colorful placeholder image
        image = Image.new('RGB', size, color=self._get_texture_color(texture_type))
        draw = ImageDraw.Draw(image)
        
        # Add some simple patterns
        if texture_type == "background":
            # Gradient-like effect
            for i in range(0, size[1], 20):
                color_intensity = int(255 * (1 - i / size[1]))
                draw.rectangle([0, i, size[0], i + 10], 
                             fill=(color_intensity, color_intensity // 2, color_intensity // 3))
        elif texture_type == "platform":
            # Block pattern
            for x in range(0, size[0], 32):
                for y in range(0, size[1], 16):
                    draw.rectangle([x, y, x + 30, y + 14], 
                                 outline=(255, 255, 255), width=2)
        elif texture_type in ["enemy", "boss"]:
            # Simple character outline
            center_x, center_y = size[0] // 2, size[1] // 2
            radius = min(size) // 4
            draw.ellipse([center_x - radius, center_y - radius, 
                         center_x + radius, center_y + radius], 
                        fill=(255, 100, 100), outline=(255, 255, 255), width=3)
        
        # Add text label
        try:
            # Try to load a font, fall back to default if not available
            font = ImageFont.load_default()
        except:
            font = None
        
        text = f"{texture_type.upper()}\nL{level_num}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size[0] - text_width) // 2
        text_y = (size[1] - text_height) // 2
        
        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
        
        # Save the image
        filename = self._save_texture_image(image, texture_type, level_num)
        
        return image, filename
    
    def _get_texture_color(self, texture_type):
        """Get base color for texture type"""
        colors = {
            "background": (135, 206, 235),  # Sky blue
            "platform": (139, 69, 19),     # Brown
            "enemy": (220, 20, 60),        # Crimson
            "boss": (128, 0, 128)          # Purple
        }
        return colors.get(texture_type, (128, 128, 128))
    
    def _save_texture_image(self, image, texture_type, level_num):
        """Save texture image to both game and verification directories"""
        # Game texture filename
        game_filename = os.path.join(self.texture_dir, f"level_{level_num}_{texture_type}.png")
        
        # Verification filename
        verification_filename = os.path.join(
            self.verification_dir, 
            f"pixellab_level_{level_num}_{texture_type}.png"
        )
        
        # Save to both locations
        image.save(game_filename)
        image.save(verification_filename)
        
        print(f"📋 Verification copy: {verification_filename}")
        
        return game_filename
    
    def _save_descriptions(self, descriptions, level_num):
        """Save texture descriptions to JSON file"""
        filename = os.path.join(self.texture_dir, f"level_{level_num}_descriptions.json")
        with open(filename, 'w') as f:
            json.dump(descriptions, f, indent=2)
        print(f"💾 Saved level {level_num} descriptions to {filename}")
    
    def set_theme(self, theme_name):
        """Change the current theme"""
        if theme_name in self.prompt_config["themes"]:
            self.current_theme = theme_name
            # Clear cache when theme changes
            self.description_cache.clear()
            print(f"🎨 Theme changed to: {theme_name}")
        else:
            print(f"❌ Theme '{theme_name}' not found")
    
    def get_available_themes(self):
        """Get list of available themes"""
        return list(self.prompt_config["themes"].keys())
    
    def add_theme(self, theme_name, theme_data):
        """Add a new theme to the configuration"""
        self.prompt_config["themes"][theme_name] = theme_data
        self._save_prompt_config()
        print(f"✅ Added new theme: {theme_name}")
    
    def _save_prompt_config(self):
        """Save prompt configuration to file"""
        config_path = os.path.join(self.base_dir, "prompt_config.json")
        with open(config_path, 'w') as f:
            json.dump(self.prompt_config, f, indent=2)


# Convenience function for backward compatibility
def create_ai_pipeline():
    """Create and return an AI pipeline instance"""
    return AITexturePipeline()


if __name__ == "__main__":
    # Test the pipeline
    pipeline = AITexturePipeline()
    print(f"Available themes: {pipeline.get_available_themes()}")
    
    # Generate textures for testing
    texture_files = pipeline.generate_all_textures(num_levels=3)
    print(f"Generated texture files: {texture_files}")
