import pygame
from settings import *
import os
import pygame
import random
from sprites import Platform, Enemy, LootChest, HealthPickup
from settings import *
from texture_generator import TextureGenerator
from pixel_lab_integration import PixelLabIntegration

class Level:
    def __init__(self, level_num):
        self.level_num = level_num
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.chests = pygame.sprite.Group()
        self.health_pickups = pygame.sprite.Group()
        self.width = 3200  # Longer level width
        self.height = WINDOW_HEIGHT
        
        # Player movement capabilities for platform accessibility validation
        self.max_jump_height = 160  # Maximum height player can jump (pixels)
        self.max_jump_distance = 180  # Maximum horizontal distance player can jump (pixels)
        
        # Create directories for storing textures if they don't exist
        self.texture_dir = os.path.join(os.path.dirname(__file__), "assets", "textures")
        os.makedirs(self.texture_dir, exist_ok=True)
        
        # Initialize texture generators
        self.texture_generator = TextureGenerator()
        self.pixel_lab = PixelLabIntegration()
        
        # Store textures for each level
        self.level_textures = {}
        
        # Generate textures for all levels
        self.generate_level_textures()
        
    def validate_platform_accessibility(self, ground_segments, platforms):
        """Ensure all platforms are accessible by checking jump heights and distances"""
        # Convert ground segments and platforms to a list of rectangles for easier processing
        all_platforms = []
        for x, y, width, height in ground_segments:
            all_platforms.append(pygame.Rect(x, y, width, height))
        
        # Add existing platforms to the list
        platform_rects = []
        for platform in platforms:
            platform_rects.append(pygame.Rect(platform.rect.x, platform.rect.y, platform.rect.width, platform.rect.height))
        
        # Sort platforms by height (y-coordinate) from lowest to highest
        platform_rects.sort(key=lambda r: r.y, reverse=True)
        
        # Start with ground segments as accessible
        accessible_platforms = all_platforms.copy()
        inaccessible_platforms = platform_rects.copy()
        
        # Keep checking until no more platforms become accessible or all are accessible
        while inaccessible_platforms and len(inaccessible_platforms) != len(platform_rects):
            newly_accessible = []
            
            for platform in inaccessible_platforms:
                # Check if this platform is reachable from any accessible platform
                for access_point in accessible_platforms:
                    # Check vertical distance (jump height)
                    height_diff = access_point.y - platform.y
                    
                    # Check horizontal distance and overlap
                    if access_point.right < platform.left:
                        # Access point is to the left of platform
                        horiz_dist = platform.left - access_point.right
                    elif access_point.left > platform.right:
                        # Access point is to the right of platform
                        horiz_dist = access_point.left - platform.right
                    else:
                        # Platforms overlap horizontally
                        horiz_dist = 0
                    
                    # If within jump range, mark as accessible
                    if 0 <= height_diff <= self.max_jump_height and horiz_dist <= self.max_jump_distance:
                        newly_accessible.append(platform)
                        break
            
            # If no new platforms became accessible, we're done
            if not newly_accessible:
                break
            
            # Add newly accessible platforms to accessible list and remove from inaccessible
            for platform in newly_accessible:
                accessible_platforms.append(platform)
                inaccessible_platforms.remove(platform)
        
        # Return list of inaccessible platforms that need adjustment
        return inaccessible_platforms
    
    def adjust_inaccessible_platforms(self, inaccessible_platforms, platform_objects):
        """Adjust positions of inaccessible platforms to make them reachable"""
        # For each inaccessible platform, find the nearest accessible platform or ground
        # and adjust its position to be reachable
        for i, platform_rect in enumerate(inaccessible_platforms):
            # Find the corresponding platform object
            for platform in platform_objects:
                if platform.rect.x == platform_rect.x and platform.rect.y == platform_rect.y:
                    # Lower the platform to make it accessible
                    new_y = platform.rect.y + 50
                    if new_y > self.height - 100:
                        new_y = self.height - 100
                    
                    # Update the platform position
                    platform.rect.y = new_y
                    print(f"Adjusted platform at ({platform.rect.x}, {platform.rect.y}) to make it accessible")
                    break
    
    def generate_level_textures(self):
        """Generate textures for all three levels"""
        try:
            # Generate texture descriptions using ChatGPT
            level_descriptions = self.texture_generator.generate_all_level_textures()
            
            # Generate texture images using Pixel Lab
            self.level_textures = self.pixel_lab.generate_all_textures_from_descriptions(level_descriptions)
            
        except Exception as e:
            print(f"Error generating textures: {e}")
            print("Using default textures instead")
            # Initialize empty texture dictionary
            self.level_textures = {1: {}, 2: {}, 3: {}}
            
        print("Generated textures for all levels")
        return True
    
    def load_level_textures(self, level_num):
        """Load textures for a specific level"""
        textures = {}
        
        if level_num in self.level_textures:
            for texture_type, filename in self.level_textures[level_num].items():
                if os.path.exists(filename):
                    try:
                        # Load the texture image
                        image = pygame.image.load(filename).convert_alpha()
                        textures[texture_type] = image
                    except Exception as e:
                        print(f"Error loading texture {filename}: {e}")
        
        return textures
    
    def create_level(self, level_num):
        """Create a level with the specified number"""
        # Clear existing sprites
        self.platforms.empty()
        self.enemies.empty()
        self.chests.empty()
        self.health_pickups.empty()
        
        # Load textures for this level
        textures = self.load_level_textures(level_num)
        
        # Create the requested level
        if level_num == 1:
            platforms, enemies, chests, health_pickups, background = self.create_level1(textures)
        elif level_num == 2:
            platforms, enemies, chests, health_pickups, background = self.create_level2(textures)
        elif level_num == 3:
            platforms, enemies, chests, health_pickups, background = self.create_level3(textures)
        else:
            platforms, enemies, chests, health_pickups, background = self.create_level1(textures)  # Default to level 1
        
        # Validate and fix platform accessibility
        self.validate_and_fix_platforms(level_num)
        
        return platforms, enemies, chests, health_pickups, background
        
    def validate_and_fix_platforms(self, level_num):
        """Check if all platforms are accessible and fix any that aren't"""
        print(f"Validating platform accessibility for level {level_num}...")
        
        # Get all ground platforms (those at the bottom of the screen)
        ground_platforms = []
        floating_platforms = []
        
        for platform in self.platforms:
            # Consider platforms near the bottom of the screen as ground
            if platform.rect.bottom >= self.height - 60:
                ground_platforms.append(platform)
            else:
                floating_platforms.append(platform)
        
        # Convert ground platforms to rectangles for accessibility checking
        ground_rects = []
        for platform in ground_platforms:
            ground_rects.append((platform.rect.x, platform.rect.y, platform.rect.width, platform.rect.height))
        
        # Check accessibility of floating platforms
        inaccessible_platforms = self.validate_platform_accessibility(ground_rects, floating_platforms)
        
        # Fix any inaccessible platforms
        if inaccessible_platforms:
            print(f"Found {len(inaccessible_platforms)} inaccessible platforms in level {level_num}. Adjusting...")
            self.adjust_inaccessible_platforms(inaccessible_platforms, floating_platforms)
        else:
            print(f"All platforms in level {level_num} are accessible!")
        
        return True
    
    def ensure_platform_accessibility(self, ground_segments, level_platforms, level_num):
        """Ensure all platforms are accessible by validating and adjusting their positions"""
        # Validate platform accessibility
        inaccessible_platforms = self.validate_platform_accessibility(ground_segments, level_platforms)
        
        # Adjust any inaccessible platforms
        if inaccessible_platforms:
            print(f"Found {len(inaccessible_platforms)} inaccessible platforms in level {level_num}. Adjusting...")
            self.adjust_inaccessible_platforms(inaccessible_platforms, level_platforms)
        else:
            print(f"All platforms in level {level_num} are accessible.")
    
    def create_level1(self, textures=None):
        """Create the first level with platforms, enemies and chests"""
        # Create ground with segments and gaps
        ground_segments = [
            (0, WINDOW_HEIGHT - 50, 800, 50),
            (950, WINDOW_HEIGHT - 50, 500, 50),
            (1600, WINDOW_HEIGHT - 50, 600, 50),
            (2400, WINDOW_HEIGHT - 50, 800, 50)
        ]
        
        platforms = []
        for x, y, width, height in ground_segments:
            ground = Platform(x, y, width, height)
            if textures and "platform" in textures:
                ground.set_texture(textures["platform"])
            self.platforms.add(ground)
            platforms.append(ground)
        
        # Create platforms - now spanning the entire longer level
        platform_positions = [
            # Starting area - create a path upward
            (100, 400, 200, 20),
            (400, 300, 200, 20),
            (200, 200, 200, 20),
            
            # Middle section - create a zigzag pattern with proper spacing
            (650, 350, 150, 20),
            (850, 250, 150, 20),
            (1050, 350, 150, 20),
            (1250, 450, 150, 20),
            (1450, 350, 150, 20),
            (1650, 250, 150, 20),
            
            # Challenging section - create stepping stones with proper spacing
            (1900, 400, 100, 20),
            (2050, 350, 100, 20),
            (2200, 300, 100, 20),
            (2350, 250, 100, 20),
            (2500, 300, 100, 20),
            (2650, 350, 100, 20),
            (2800, 400, 100, 20),
            
            # Final section
            (3000, 300, 150, 20)
        ]
        
        # Create platform objects
        level_platforms = []
        for x, y, width, height in platform_positions:
            platform = Platform(x, y, width, height)
            if textures and "platform" in textures:
                platform.set_texture(textures["platform"])
            self.platforms.add(platform)
            level_platforms.append(platform)
        
        # Ensure all platforms are accessible
        self.ensure_platform_accessibility(ground_segments, level_platforms, 1)
        
        # Add enemies throughout the level
        enemy_positions = [
            # Starting area enemies
            (150, WINDOW_HEIGHT - 100, platforms[0]),  # Ground
            (450, WINDOW_HEIGHT - 100, platforms[0]),  # Ground
            (150, 360, level_platforms[0]),  # First platform
            
            # Middle section enemies
            (700, 310, level_platforms[3]),  # Platform
            (1100, 310, level_platforms[5]),  # Platform
            (1500, 310, level_platforms[7]),  # Platform
            
            # Challenging section enemies
            (1950, 360, level_platforms[9]),  # Platform
            (2250, 260, level_platforms[12]),  # Platform
            (2550, 260, level_platforms[14]),  # Platform
            
            # Final section enemies
            (2850, 360, level_platforms[16]),  # Platform
            (3050, WINDOW_HEIGHT - 100, platforms[3])  # Ground
        ]
        
        for x, y, platform in enemy_positions:
            enemy = Enemy(x, y, platform)
            if textures and "enemy" in textures:
                enemy.set_texture(textures["enemy"])
            self.enemies.add(enemy)
        
        # Add loot chests throughout the level
        chest_positions = [
            # Starting area chests
            (200, 380),
            (400, 280),
            
            # Middle section chests
            (800, 380),
            (1200, 280),
            (1600, 380),
            
            # Challenging section chests
            (2000, 280),
            (2400, 380),
            
            # Final section chests
            (2800, 280),
            (3100, 380)
        ]
        
        for x, y in chest_positions:
            chest = LootChest(x, y)
            self.chests.add(chest)
            
        # Add health pickups strategically placed in challenging areas
        health_pickup_positions = [
            # Near gaps
            (875, 200),  # Between first and second ground segments
            (1550, 400), # Between second and third ground segments
            (2350, 200), # In the challenging section
            
            # Near difficult enemy encounters
            (700, 280),  # Near middle section enemy
            (2550, 230), # Near challenging section enemy
            (3050, 250)  # Near final section enemy
        ]
        
        for x, y in health_pickup_positions:
            health_pickup = HealthPickup(x, y)
            self.health_pickups.add(health_pickup)
        
        # Set background texture
        background = None
        if textures and "background" in textures:
            background = textures["background"]
        
        return self.platforms, self.enemies, self.chests, self.health_pickups, background
    
    def create_level2(self, textures=None):
        """Create the second level with platforms, enemies and chests"""
        # Create ground with multiple segments and larger gaps
        ground_segments = [
            (0, WINDOW_HEIGHT - 50, 600, 50),
            (800, WINDOW_HEIGHT - 50, 500, 50),
            (1500, WINDOW_HEIGHT - 50, 400, 50),
            (2100, WINDOW_HEIGHT - 50, 600, 50),
            (2900, WINDOW_HEIGHT - 50, 300, 50)
        ]
        
        platforms = []
        for x, y, width, height in ground_segments:
            ground = Platform(x, y, width, height)
            if textures and "platform" in textures:
                ground.set_texture(textures["platform"])
            self.platforms.add(ground)
            platforms.append(ground)
        
        # Create platforms - more complex layout for level 2 with vertical challenges
        platform_positions = [
            # Starting area - ascending platforms
            (100, 450, 150, 20),
            (300, 400, 150, 20),
            (500, 350, 150, 20),
            
            # First gap challenge
            (700, 300, 80, 20),
            (900, 350, 80, 20),
            
            # Middle section - zigzag platforms
            (1100, 400, 120, 20),
            (1300, 350, 120, 20),
            (1500, 300, 120, 20),
            (1700, 250, 120, 20),
            (1900, 300, 120, 20),
            
            # Advanced section - floating islands
            (2100, 350, 100, 20),
            (2250, 300, 100, 20),
            (2400, 250, 100, 20),
            (2550, 200, 100, 20),
            (2700, 250, 100, 20),
            (2850, 300, 100, 20),
            
            # Vertical challenge section
            (2200, 450, 80, 20),
            (2400, 400, 80, 20),
            (2600, 450, 80, 20),
            
            # Final approach
            (3000, 350, 150, 20)
        ]
        
        level_platforms = []
        for x, y, width, height in platform_positions:
            platform = Platform(x, y, width, height)
            if textures and "platform" in textures:
                platform.set_texture(textures["platform"])
            self.platforms.add(platform)
            level_platforms.append(platform)
        
        # Add enemies on platforms - more enemies for level 2
        enemy_positions = [
            # Ground enemies
            (200, WINDOW_HEIGHT - 100, platforms[0]),
            (900, WINDOW_HEIGHT - 100, platforms[1]),
            (1600, WINDOW_HEIGHT - 100, platforms[2]),
            (2300, WINDOW_HEIGHT - 100, platforms[3]),
            
            # Platform enemies - starting area
            (150, 410, level_platforms[0]),
            (350, 360, level_platforms[1]),
            (550, 310, level_platforms[2]),
            
            # Middle section enemies
            (1150, 360, level_platforms[5]),
            (1350, 310, level_platforms[6]),
            (1550, 260, level_platforms[7]),
            (1750, 210, level_platforms[8]),
            
            # Advanced section enemies
            (2150, 310, level_platforms[10]),
            (2450, 210, level_platforms[12]),
            (2750, 210, level_platforms[14]),
            
            # Final approach enemy
            (3050, 310, level_platforms[20])
        ]
        
        for x, y, platform in enemy_positions:
            enemy = Enemy(x, y, platform)
            if textures and "enemy" in textures:
                enemy.set_texture(textures["enemy"])
            # Make level 2 enemies stronger
            enemy.health = 75
            self.enemies.add(enemy)
        
        # Add loot chests throughout the extended level
        chest_positions = [
            # Starting area chests
            (150, 430),  # Near first platform
            (350, 380),  # Near second platform
            (550, 330),  # Near third platform
            
            # Middle section chests
            (900, 330),   # After first gap
            (1200, 380),  # Middle zigzag
            (1600, 280),  # End of zigzag
            
            # Advanced section chests
            (2150, 330),  # Floating islands
            (2450, 230),  # Higher platforms
            (2700, 230),  # Last floating island
            
            # Final approach chest
            (3050, 330)   # Final platform
        ]
        
        for x, y in chest_positions:
            chest = LootChest(x, y)
            # Level 2 chests have better loot
            chest.loot_value = random.randint(30, 80)
            self.chests.add(chest)
            
        # Add health pickups in strategic locations
        health_pickup_positions = [
            # Near gaps
            (700, 250),  # Above the first gap challenge
            (1350, 200), # Above middle zigzag
            (2300, 150), # Above the advanced section
            
            # Near difficult enemy encounters
            (900, 300),  # Near middle section enemy
            (1750, 180), # Near challenging section enemy
            (3050, 280)  # Near final approach enemy
        ]
        
        for x, y in health_pickup_positions:
            health_pickup = HealthPickup(x, y, health_value=35)  # Level 2 health pickups give more health
            self.health_pickups.add(health_pickup)
        
        # Set background texture
        background = None
        if textures and "background" in textures:
            background = textures["background"]
        
        return self.platforms, self.enemies, self.chests, self.health_pickups, background
    
    def create_level3(self, textures=None):
        """Create the third level with platforms, enemies, chests and a boss"""
        # Create ground with more challenging gaps
        ground_segments = [
            (0, WINDOW_HEIGHT - 50, 500, 50),     # Starting ground
            (700, WINDOW_HEIGHT - 50, 300, 50),   # First island
            (1200, WINDOW_HEIGHT - 50, 300, 50),  # Second island
            (1700, WINDOW_HEIGHT - 50, 300, 50),  # Third island
            (2200, WINDOW_HEIGHT - 50, 300, 50),  # Fourth island
            (2800, WINDOW_HEIGHT - 50, 400, 50)   # Boss arena
        ]
        
        platforms = []
        for x, y, width, height in ground_segments:
            ground = Platform(x, y, width, height)
            if textures and "platform" in textures:
                ground.set_texture(textures["platform"])
            self.platforms.add(ground)
            platforms.append(ground)
        
        # Create platforms - most complex layout for level 3
        platform_positions = [
            # Starting area - vertical challenge
            (100, 500, 100, 20),
            (250, 450, 100, 20),
            (400, 400, 100, 20),
            (250, 350, 100, 20),
            (100, 300, 100, 20),
            
            # First gap crossing
            (550, 350, 80, 20),
            (650, 300, 80, 20),
            
            # First island platforms
            (750, 400, 100, 20),
            (850, 350, 100, 20),
            (950, 300, 100, 20),
            
            # Second gap crossing - harder
            (1050, 250, 60, 20),
            (1130, 200, 60, 20),
            
            # Second island - zigzag up
            (1250, 250, 80, 20),
            (1350, 300, 80, 20),
            (1450, 250, 80, 20),
            
            # Third gap crossing - even harder
            (1550, 200, 50, 20),
            (1620, 150, 50, 20),
            (1690, 200, 50, 20),
            
            # Third island - vertical challenge
            (1750, 300, 80, 20),
            (1850, 250, 80, 20),
            (1950, 200, 80, 20),
            (2050, 250, 80, 20),
            (2150, 300, 80, 20),
            
            # Final approach
            (2350, 350, 60, 20),
            (2450, 300, 60, 20),
            (2550, 250, 60, 20),
            (2650, 300, 60, 20),
            
            # Boss arena platforms
            (2900, 400, 200, 20),  # Boss platform
            (2850, 300, 80, 20),    # Upper platforms for player
            (3050, 300, 80, 20)
        ]
        
        level_platforms = []
        for x, y, width, height in platform_positions:
            platform = Platform(x, y, width, height)
            if textures and "platform" in textures:
                platform.set_texture(textures["platform"])
            self.platforms.add(platform)
            level_platforms.append(platform)
        
        # Add enemies on platforms - most enemies for level 3
        enemy_positions = [
            # Ground enemies
            (200, WINDOW_HEIGHT - 100, platforms[0]),
            (800, WINDOW_HEIGHT - 100, platforms[1]),
            (1300, WINDOW_HEIGHT - 100, platforms[2]),
            (1800, WINDOW_HEIGHT - 100, platforms[3]),
            (2300, WINDOW_HEIGHT - 100, platforms[4]),
            
            # Starting area enemies
            (130, 460, level_platforms[0]),
            (280, 410, level_platforms[1]),
            (430, 360, level_platforms[2]),
            
            # First island enemies
            (780, 360, level_platforms[7]),
            (880, 310, level_platforms[8]),
            (980, 260, level_platforms[9]),
            
            # Second island enemies
            (1280, 210, level_platforms[13]),
            (1380, 260, level_platforms[14]),
            (1480, 210, level_platforms[15]),
            
            # Third island enemies - tougher
            (1780, 260, level_platforms[19]),
            (1880, 210, level_platforms[20]),
            (1980, 160, level_platforms[21]),
            (2080, 210, level_platforms[22]),
            (2180, 260, level_platforms[23]),
            
            # Final approach enemies - very tough
            (2380, 310, level_platforms[24]),
            (2480, 260, level_platforms[25]),
            (2580, 210, level_platforms[26]),
            (2680, 260, level_platforms[27])
        ]
        
        for x, y, platform in enemy_positions:
            enemy = Enemy(x, y, platform)
            if textures and "enemy" in textures:
                enemy.set_texture(textures["enemy"])
            # Make level 3 enemies even stronger
            enemy.health = 100
            self.enemies.add(enemy)
        
        # Add boss enemy on the boss platform at the end of the level
        boss = Enemy(3000, 360, level_platforms[30])  # Boss platform at the end
        if textures and "boss" in textures:
            boss.set_texture(textures["boss"])
        # Make boss much stronger
        boss.health = 300
        boss.image = pygame.Surface((60, 80))  # Bigger boss
        boss.image.fill(RED)  # Default color if no texture
        boss.rect = boss.image.get_rect()
        boss.rect.x = 3000
        boss.rect.y = 320  # Position on the platform
        self.enemies.add(boss)
        
        # Add loot chests throughout the extended level
        chest_positions = [
            # Starting area chests
            (130, 480),  # First platform
            (250, 430),  # Second platform
            (400, 380),  # Third platform
            
            # First gap crossing chests
            (600, 330),  # Gap platform
            
            # First island chests
            (800, 380),  # First island platform
            (950, 280),  # Higher platform
            
            # Second island chests
            (1300, 230),  # Second island platform
            (1450, 230),  # Zigzag platform
            
            # Third island chests - better rewards
            (1800, 280),  # Third island platform
            (2000, 180),  # Higher platform
            
            # Final approach chests - best rewards
            (2400, 330),  # Approach platform
            (2600, 230),  # Higher platform
            
            # Boss arena chest - special reward
            (3000, 380)   # Special chest near boss
        ]
        
        for i, (x, y) in enumerate(chest_positions):
            chest = LootChest(x, y)
            # Level 3 chests have best loot
            if i < 8:  # First half of chests
                chest.loot_value = random.randint(50, 80)
            elif i < 12:  # Second half of chests (better rewards)
                chest.loot_value = random.randint(70, 100)
            else:  # Final approach chests
                chest.loot_value = random.randint(90, 120)
                
            # Special chest near boss has guaranteed high value
            if i == len(chest_positions) - 1:  # Last chest is special
                chest.loot_value = 200
            self.chests.add(chest)
        
        # Add health pickups in strategic locations for level 3
        health_pickup_positions = [
            # Starting area - to help with the vertical challenge
            (250, 320),  # Above the starting vertical challenge
            
            # Gap crossings - placed to help with difficult jumps
            (600, 280),  # First gap crossing
            (1090, 180),  # Second gap crossing
            (1585, 130),  # Third gap crossing (hardest one)
            
            # Island platforms - for recovery after difficult sections
            (950, 250),  # First island high platform
            (1450, 200),  # Second island zigzag
            (2050, 180),  # Third island vertical challenge
            
            # Final approach and boss arena - critical healing
            (2500, 230),  # During final approach
            (2850, 250),  # Upper platform in boss arena
            (3050, 250)   # Upper platform on other side of boss arena
        ]
        
        for i, (x, y) in enumerate(health_pickup_positions):
            # Boss arena health pickups give more health
            health_value = 50 if i >= 7 else 40
            health_pickup = HealthPickup(x, y, health_value=health_value)
            self.health_pickups.add(health_pickup)
        
        # Set background texture
        background = None
        if textures and "background" in textures:
            background = textures["background"]
        
        return self.platforms, self.enemies, self.chests, self.health_pickups, background
