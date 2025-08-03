import pygame
from settings import *
import os
import random
from sprites import Platform, Enemy, LootChest, HealthPickup, Door
from texture_generator import TextureGenerator
from pixel_lab_integration import PixelLabIntegration

class Level:
    def __init__(self, level_num, is_boss_room=False):
        self.level_num = level_num
        self.is_boss_room = is_boss_room
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.chests = pygame.sprite.Group()
        self.health_pickups = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.width = 3200 if not is_boss_room else 1600  # Boss rooms are smaller
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
    
    def create_level(self, level_num, is_boss_room=False):
        """Create a level with the specified number"""
        # Clear existing sprites
        self.platforms.empty()
        self.enemies.empty()
        self.chests.empty()
        self.health_pickups.empty()
        self.doors.empty()
        
        # Set boss room flag
        self.is_boss_room = is_boss_room
        
        # Load textures for this level
        textures = self.load_level_textures(level_num)
        
        # Create the requested level
        if is_boss_room:
            # Create boss room for the specified level
            platforms, enemies, chests, health_pickups, background = self.create_boss_room(level_num, textures)
        else:
            # Create regular level
            if level_num == 1:
                platforms, enemies, chests, health_pickups, door, background = self.create_level1(textures)
            elif level_num == 2:
                platforms, enemies, chests, health_pickups, door, background = self.create_level2(textures)
            elif level_num == 3:
                platforms, enemies, chests, health_pickups, door, background = self.create_level3(textures)
            else:
                platforms, enemies, chests, health_pickups, door, background = self.create_level1(textures)  # Default to level 1
        
        # Validate and fix platform accessibility
        self.validate_and_fix_platforms(level_num)
        
        if is_boss_room:
            return platforms, enemies, chests, health_pickups, pygame.sprite.Group(), background
        else:
            return platforms, enemies, chests, health_pickups, door, background
        
    def create_boss_room(self, level_num, textures=None):
        """Create a boss room for the specified level"""
        # Boss rooms are smaller and focused on the boss fight
        self.width = 1600
        
        # Create ground
        ground = Platform(0, WINDOW_HEIGHT - 50, self.width, 50)
        if textures and "platform" in textures:
            ground.set_texture(textures["platform"])
        self.platforms.add(ground)
        
        # Add some platforms for movement variety
        platform_positions = [
            # Side platforms
            (200, 400, 200, 20),
            (1200, 400, 200, 20),
            # Middle platform
            (700, 350, 200, 20)
        ]
        
        for x, y, width, height in platform_positions:
            platform = Platform(x, y, width, height)
            if textures and "platform" in textures:
                platform.set_texture(textures["platform"])
            self.platforms.add(platform)
        
        # Create a boss enemy based on the level
        boss_x = self.width // 2
        boss_y = WINDOW_HEIGHT - 100
        boss = Enemy(boss_x, boss_y, None, "boss")
        if textures and "boss" in textures:
            boss.set_texture(textures["boss"])
        self.enemies.add(boss)
        
        # Add a few health pickups for the boss fight
        health_pickup_positions = [
            (300, 350),
            (1300, 350),
            (800, 300)
        ]
        
        for x, y in health_pickup_positions:
            health_pickup = HealthPickup(x, y)
            self.health_pickups.add(health_pickup)
        
        # Set background texture
        background = None
        if textures and "background" in textures:
            background = textures["background"]
        
        # Add a door at the end of the level on the final platform
        # Final platform is at (3000, 300, 150, 20)
        door_x = 3050  # Center of the final platform
        door_y = 300 + 80  # Position door so its bottom sits on platform (Door class subtracts 80)
        door = Door(door_x, door_y)
        self.doors.add(door)
        
        return self.platforms, self.enemies, self.chests, self.health_pickups, self.doors, background
        
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
        
        # Create platforms - now spanning the entire longer level with proper clearance
        platform_positions = [
            # Starting area - create a path upward with 80+ pixel spacing
            (100, 420, 200, 20),   # Raised from 400 to 420
            (400, 320, 200, 20),   # Raised from 300 to 320  
            (200, 220, 200, 20),   # Raised from 200 to 220
            
            # Middle section - create a zigzag pattern with proper spacing
            (650, 380, 150, 20),   # Raised from 350 to 380
            (850, 280, 150, 20),   # Raised from 250 to 280
            (1050, 380, 150, 20),  # Raised from 350 to 380
            (1250, 470, 150, 20),  # Raised from 450 to 470
            (1450, 380, 150, 20),  # Raised from 350 to 380
            (1650, 280, 150, 20),  # Raised from 250 to 280
            
            # Challenging section - create stepping stones with proper spacing
            (1900, 420, 100, 20),  # Raised from 400 to 420
            (2050, 370, 100, 20),  # Raised from 350 to 370
            (2200, 320, 100, 20),  # Raised from 300 to 320
            (2350, 270, 100, 20),  # Raised from 250 to 270
            (2500, 320, 100, 20),  # Raised from 300 to 320
            (2650, 370, 100, 20),  # Raised from 350 to 370
            (2800, 420, 100, 20),  # Raised from 400 to 420
            
            # Final section
            (3000, 320, 150, 20)   # Raised from 300 to 320
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
        
        # Add one loot chest next to the door
        chest_x = 3000  # Left side of the door (door is at 3050)
        chest_y = 380   # Same level as door platform
        chest = LootChest(chest_x, chest_y)
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
        
        # Add a door at the end of the level on the final platform
        # Final platform is at (3000, 350, 150, 20)
        door_x = 3050  # Center of the final platform
        door_y = 350 + 80  # Position door so its bottom sits on platform (Door class subtracts 80)
        door = Door(door_x, door_y)
        self.doors.add(door)
        
        return self.platforms, self.enemies, self.chests, self.health_pickups, self.doors, background
    
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
        
        # Create platforms - more complex layout for level 2 with proper clearance
        platform_positions = [
            # Starting area - ascending platforms with 80+ pixel spacing
            (100, 470, 150, 20),   # Raised from 450 to 470
            (300, 420, 150, 20),   # Raised from 400 to 420
            (500, 370, 150, 20),   # Raised from 350 to 370
            
            # First gap challenge
            (700, 320, 80, 20),    # Raised from 300 to 320
            (900, 370, 80, 20),    # Raised from 350 to 370
            
            # Middle section - zigzag platforms
            (1100, 420, 120, 20),  # Raised from 400 to 420
            (1300, 370, 120, 20),  # Raised from 350 to 370
            (1500, 320, 120, 20),  # Raised from 300 to 320
            (1700, 270, 120, 20),  # Raised from 250 to 270
            (1900, 320, 120, 20),  # Raised from 300 to 320
            
            # Advanced section - floating islands
            (2100, 370, 100, 20),  # Raised from 350 to 370
            (2250, 320, 100, 20),  # Raised from 300 to 320
            (2400, 270, 100, 20),  # Raised from 250 to 270
            (2550, 220, 100, 20),  # Raised from 200 to 220
            (2700, 270, 100, 20),  # Raised from 250 to 270
            (2850, 320, 100, 20),  # Raised from 300 to 320
            
            # Vertical challenge section
            (2200, 470, 80, 20),   # Raised from 450 to 470
            (2400, 420, 80, 20),   # Raised from 400 to 420
            (2600, 470, 80, 20),   # Raised from 450 to 470
            
            # Final approach
            (3000, 370, 150, 20)   # Raised from 350 to 370
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
            (3050, 310, level_platforms[19])  # Fixed: use last platform (index 19)
        ]
        
        for x, y, platform in enemy_positions:
            enemy = Enemy(x, y, platform)
            if textures and "enemy" in textures:
                enemy.set_texture(textures["enemy"])
            # Make level 2 enemies stronger
            enemy.health = 75
            self.enemies.add(enemy)
        
        # Add one loot chest next to the door (matching level 1 pattern)
        chest_x = 2950  # Left side of the door (door is at 3000)
        chest_y = 330   # Same level as door platform
        chest = LootChest(chest_x, chest_y)
        # Level 2 chest has better loot
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
        
        # Add a door at the end of the level on the final platform
        # Final platform is at (3050, 300, 80, 20)
        door_x = 3050  # Center of the final platform
        door_y = 300 + 80  # Position door so its bottom sits on platform (Door class subtracts 80)
        door = Door(door_x, door_y)
        self.doors.add(door)
        
        return self.platforms, self.enemies, self.chests, self.health_pickups, self.doors, background
    
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
            # Starting area - vertical challenge with proper clearance
            (100, 500, 100, 20),   # Keep at 500 (good spacing from ground)
            (250, 450, 100, 20),   # Keep at 450 (50 pixel gap - acceptable)
            (400, 420, 100, 20),   # Raised from 400 to 420
            (250, 370, 100, 20),   # Raised from 350 to 370
            (100, 320, 100, 20),   # Raised from 300 to 320
            
            # First gap crossing
            (550, 370, 80, 20),    # Raised from 350 to 370
            (650, 320, 80, 20),    # Raised from 300 to 320
            
            # First island platforms
            (750, 420, 100, 20),   # Raised from 400 to 420
            (850, 370, 100, 20),   # Raised from 350 to 370
            (950, 320, 100, 20),   # Raised from 300 to 320
            
            # Second gap crossing - harder
            (1050, 270, 60, 20),   # Raised from 250 to 270
            (1130, 220, 60, 20),   # Raised from 200 to 220
            
            # Second island - zigzag up
            (1250, 270, 80, 20),   # Raised from 250 to 270
            (1350, 320, 80, 20),   # Raised from 300 to 320
            (1450, 270, 80, 20),   # Raised from 250 to 270
            
            # Third gap crossing - even harder
            (1550, 220, 50, 20),   # Raised from 200 to 220
            (1620, 170, 50, 20),   # Raised from 150 to 170
            (1690, 220, 50, 20),   # Raised from 200 to 220
            
            # Third island - vertical challenge
            (1750, 320, 80, 20),   # Raised from 300 to 320
            (1850, 270, 80, 20),   # Raised from 250 to 270
            (1950, 220, 80, 20),   # Raised from 200 to 220
            (2050, 270, 80, 20),   # Raised from 250 to 270
            (2150, 320, 80, 20),   # Raised from 300 to 320
            
            # Final approach
            (2350, 370, 60, 20),   # Raised from 350 to 370
            (2450, 320, 60, 20),   # Raised from 300 to 320
            (2550, 270, 60, 20),   # Raised from 250 to 270
            (2650, 320, 60, 20),   # Raised from 300 to 320
            
            # Boss arena platforms
            (2900, 420, 200, 20),  # Raised from 400 to 420
            (2850, 320, 80, 20),   # Raised from 300 to 320
            (3050, 320, 80, 20)    # Raised from 300 to 320
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
        
        # Add one loot chest next to the door (matching level 1 pattern)
        chest_x = 2950  # Left side of the door (door is at 3000)
        chest_y = 380   # Same level as door platform
        chest = LootChest(chest_x, chest_y)
        # Level 3 chest has best loot
        chest.loot_value = random.randint(90, 120)
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
        
        # Add a door at the end of the level on the final platform
        # Final platform is at (3050, 300, 80, 20)
        door_x = 3050  # Center of the final platform
        door_y = 300 + 80  # Position door so its bottom sits on platform (Door class subtracts 80)
        door = Door(door_x, door_y)
        self.doors.add(door)
        
        return self.platforms, self.enemies, self.chests, self.health_pickups, self.doors, background
