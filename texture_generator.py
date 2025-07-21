import os
import json
import random
from io import BytesIO

# Try to import optional dependencies with fallbacks
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print("Warning: OpenAI package not available. Using fallback texture descriptions.")
    OPENAI_AVAILABLE = False

try:
    import requests
    from PIL import Image
    IMAGE_LIBS_AVAILABLE = True
except ImportError:
    print("Warning: Requests or PIL packages not available. Using fallback textures.")
    IMAGE_LIBS_AVAILABLE = False

# Constants for texture generation
THEME_OPTIONS = [
    "medieval fantasy", 
    "sci-fi futuristic", 
    "post-apocalyptic wasteland", 
    "underwater kingdom",
    "volcanic landscape", 
    "enchanted forest", 
    "desert ruins", 
    "cyberpunk city",
    "crystal caves", 
    "steampunk airship"
]

# Texture types needed for each level
TEXTURE_TYPES = [
    "background",
    "platform",
    "enemy",
    "boss"  # Only used for final level
]

class TextureGenerator:
    def __init__(self, api_key=None):
        """Initialize the texture generator with OpenAI API key"""
        # Try to get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: No OpenAI API key provided. Please set OPENAI_API_KEY environment variable.")
        
        # Set up OpenAI client if API key is available
        if self.api_key:
            openai.api_key = self.api_key
        
        # Create directories for storing textures if they don't exist
        self.texture_dir = os.path.join(os.path.dirname(__file__), "assets", "textures")
        os.makedirs(self.texture_dir, exist_ok=True)
        
        # Cache for storing generated descriptions
        self.description_cache = {}
    
    def generate_level_theme(self):
        """Generate a random theme for the level"""
        return random.choice(THEME_OPTIONS)
    
    def generate_texture_descriptions(self, level_num, theme=None):
        """Generate texture descriptions for a level based on a theme"""
        if theme is None:
            theme = self.generate_level_theme()
        
        # Cache key for this level and theme
        cache_key = f"{level_num}_{theme}"
        
        # Return cached descriptions if available
        if cache_key in self.description_cache:
            return self.description_cache[cache_key]
        
        # Prepare descriptions for each texture type
        descriptions = {}
        
        # Is this the final level? (level 3 in our case)
        is_final_level = (level_num == 3)
        
        # Generate descriptions for each texture type
        for texture_type in TEXTURE_TYPES:
            # Skip boss texture for non-final levels
            if texture_type == "boss" and not is_final_level:
                continue
                
            # Generate description using OpenAI API
            description = self._query_openai_for_description(texture_type, theme, level_num, is_final_level)
            descriptions[texture_type] = description
        
        # Cache the descriptions
        self.description_cache[cache_key] = descriptions
        return descriptions
    
    def _query_openai_for_description(self, texture_type, theme, level_num, is_final_level):
        """Query OpenAI API to get a texture description"""
        if not self.api_key or not OPENAI_AVAILABLE:
            # Return default descriptions if no API key is available or OpenAI package not installed
            return self._get_default_description(texture_type, theme, level_num)
        
        try:
            # Craft a prompt based on texture type and theme
            prompt = self._create_prompt(texture_type, theme, level_num, is_final_level)
            
            # Try to detect OpenAI API version and call appropriate method
            try:
                # New OpenAI API (v1.x)
                if hasattr(openai, 'ChatCompletion') and callable(getattr(openai.ChatCompletion, 'create', None)):
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",  # More widely available model
                        messages=[
                            {"role": "system", "content": "You are a game asset designer specializing in pixel art descriptions."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=150,
                        temperature=0.7
                    )
                    description = response.choices[0].message.content.strip()
                # Newer Client API (v0.28+)
                elif hasattr(openai, 'Client'):
                    client = openai.Client(api_key=self.api_key)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a game asset designer specializing in pixel art descriptions."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=150,
                        temperature=0.7
                    )
                    description = response.choices[0].message.content.strip()
                # Legacy API
                else:
                    response = openai.Completion.create(
                        engine="text-davinci-003",
                        prompt=f"You are a game asset designer specializing in pixel art descriptions.\n\n{prompt}",
                        max_tokens=150,
                        temperature=0.7
                    )
                    description = response.choices[0].text.strip()
                
                return description
            except AttributeError:
                # Fallback to default if API structure is unexpected
                print("Warning: OpenAI API structure not recognized. Using fallback descriptions.")
                return self._get_default_description(texture_type, theme, level_num)
            
        except Exception as e:
            print(f"Error querying OpenAI API: {e}")
            return self._get_default_description(texture_type, theme, level_num)
    
    def _create_prompt(self, texture_type, theme, level_num, is_final_level):
        """Create a prompt for the OpenAI API based on texture type and theme"""
        difficulty = "easy" if level_num == 1 else "medium" if level_num == 2 else "hard"
        
        if texture_type == "background":
            return f"Describe a pixel art background for a {difficulty} level in a 2D platformer game with a {theme} theme. The description should be detailed enough for an AI image generator to create a good background texture. Keep it under 100 words."
        
        elif texture_type == "platform":
            return f"Describe a pixel art platform texture for a {difficulty} level in a 2D platformer game with a {theme} theme. The description should be detailed enough for an AI image generator to create a good platform texture. Keep it under 100 words."
        
        elif texture_type == "enemy":
            return f"Describe a pixel art enemy character for a {difficulty} level in a 2D platformer game with a {theme} theme. The description should be detailed enough for an AI image generator to create a good enemy texture. Keep it under 100 words."
        
        elif texture_type == "boss" and is_final_level:
            return f"Describe an intimidating final boss character for a 2D platformer game with a {theme} theme. The description should be detailed enough for an AI image generator to create an impressive boss texture. Keep it under 100 words."
        
        else:
            return f"Describe a pixel art texture for a {texture_type} in a {difficulty} level with a {theme} theme. Keep it under 100 words."
    
    def _get_default_description(self, texture_type, theme, level_num):
        """Get a default description if API call fails"""
        if texture_type == "background":
            return f"A {theme} background for level {level_num} with detailed pixel art style."
        elif texture_type == "platform":
            return f"A {theme} platform with {level_num} level of detail in pixel art style."
        elif texture_type == "enemy":
            return f"A menacing {theme} enemy character for level {level_num} in pixel art style."
        elif texture_type == "boss":
            return f"An imposing final boss with {theme} elements in detailed pixel art style."
        else:
            return f"A {theme} {texture_type} texture in pixel art style."
    
    def generate_pixel_lab_prompt(self, description):
        """Convert a description into a prompt suitable for Pixel Lab"""
        # Pixel Lab might have specific formatting requirements
        # For now, we'll just add some pixel art specific keywords
        return f"pixel art, 16-bit style, game asset, {description}"
    
    def save_texture_descriptions(self, level_num, descriptions):
        """Save texture descriptions to a JSON file"""
        filename = os.path.join(self.texture_dir, f"level_{level_num}_descriptions.json")
        with open(filename, 'w') as f:
            json.dump(descriptions, f, indent=4)
        return filename
    
    def generate_all_level_textures(self):
        """Generate textures for all three levels"""
        # Generate a common theme for consistency
        theme = self.generate_level_theme()
        print(f"Generating textures with theme: {theme}")
        
        level_descriptions = {}
        
        # Generate descriptions for each level
        for level_num in range(1, 4):  # Levels 1, 2, 3
            descriptions = self.generate_texture_descriptions(level_num, theme)
            level_descriptions[level_num] = descriptions
            
            # Save descriptions to file
            filename = self.save_texture_descriptions(level_num, descriptions)
            print(f"Saved level {level_num} descriptions to {filename}")
        
        return level_descriptions


# Example usage
if __name__ == "__main__":
    # Initialize texture generator
    generator = TextureGenerator()
    
    # Generate textures for all levels
    level_descriptions = generator.generate_all_level_textures()
    
    # Print the descriptions
    for level_num, descriptions in level_descriptions.items():
        print(f"\nLevel {level_num} Textures:")
        for texture_type, description in descriptions.items():
            print(f"  {texture_type.capitalize()}: {description}")
            print(f"  Pixel Lab prompt: {generator.generate_pixel_lab_prompt(description)}")
            print()
