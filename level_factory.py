"""
Optimized Level Factory for AI Game

This module provides ultra-fast level creation through:
- Lazy loading of level components
- Pre-computed level layouts
- Minimal object creation during switching
- Smart caching strategies
"""

import pygame
import json
import os
import random
from settings import *
from sprites import Platform, Enemy, LootChest, HealthPickup, Door


class LevelTemplate:
    """Lightweight level template that stores level data without creating sprites"""
    
    def __init__(self, level_num, is_boss_room=False):
        self.level_num = level_num
        self.is_boss_room = is_boss_room
        self.width = 3200 if not is_boss_room else 1600
        self.height = WINDOW_HEIGHT
        
        # Pre-computed level data (no sprite creation)
        self.platform_data = []
        self.enemy_data = []
        self.chest_data = []
        self.health_pickup_data = []
        self.door_data = []
        
        # Generate level layout data (fast)
        self._generate_level_data()
    
    def _generate_level_data(self):
        """Generate level layout data without creating sprites (ultra-fast)"""
        if self.is_boss_room:
            self._generate_boss_room_data()
        else:
            self._generate_regular_level_data()
    
    def _generate_regular_level_data(self):
        """Generate data for regular levels"""
        # Platform positions (just coordinates, no sprites)
        platform_positions = [
            (200, 520), (400, 470), (650, 430), (850, 380),
            (1050, 430), (1250, 500), (1450, 430), (1650, 380),
            (1900, 470), (2050, 420), (2200, 370), (2350, 320),
            (2500, 370), (2650, 420), (2800, 470), (3000, 370)
        ]
        
        for i, (x, y) in enumerate(platform_positions):
            # Add some randomization based on level
            y_offset = (self.level_num - 1) * 10
            self.platform_data.append({
                'x': x, 'y': y - y_offset, 'width': 120, 'height': 20, 'id': i
            })
        
        # Enemy positions
        enemy_positions = [(300, 490), (700, 400), (1100, 400), (1500, 400), (2000, 390)]
        for i, (x, y) in enumerate(enemy_positions):
            self.enemy_data.append({
                'x': x, 'y': y, 'enemy_type': 'basic', 'id': i
            })
        
        # Chest positions
        chest_positions = [(500, 440), (1200, 470), (2100, 390)]
        for i, (x, y) in enumerate(chest_positions):
            self.chest_data.append({
                'x': x, 'y': y, 'chest_type': 'basic', 'id': i
            })
        
        # Health pickup positions
        health_positions = [(800, 350), (1600, 350), (2400, 290)]
        for i, (x, y) in enumerate(health_positions):
            self.health_pickup_data.append({
                'x': x, 'y': y, 'health_amount': 25, 'id': i
            })
        
        # Door position (end of level)
        self.door_data.append({
            'x': self.width - 100, 'y': WINDOW_HEIGHT - 120, 'door_type': 'exit', 'id': 0
        })
    
    def _generate_boss_room_data(self):
        """Generate data for boss rooms"""
        # Fewer platforms in boss room
        platform_positions = [
            (200, 520), (500, 470), (800, 420), (1100, 470), (1400, 520)
        ]
        
        for i, (x, y) in enumerate(platform_positions):
            self.platform_data.append({
                'x': x, 'y': y, 'width': 120, 'height': 20, 'id': i
            })
        
        # Boss enemy
        self.enemy_data.append({
            'x': self.width // 2, 'y': 300, 'enemy_type': 'boss', 'id': 0
        })
        
        # Victory chest
        self.chest_data.append({
            'x': self.width // 2, 'y': 490, 'chest_type': 'victory', 'id': 0
        })


class OptimizedLevel:
    """Optimized level that creates sprites only when needed"""
    
    def __init__(self, template, game_manager=None):
        self.template = template
        self.game_manager = game_manager
        
        # Sprite groups (created lazily)
        self._platforms = None
        self._enemies = None
        self._chests = None
        self._health_pickups = None
        self._doors = None
        self._background = None
        
        # Textures (loaded lazily)
        self._textures = None
    
    @property
    def level_num(self):
        return self.template.level_num
    
    @property
    def is_boss_room(self):
        return self.template.is_boss_room
    
    @property
    def width(self):
        return self.template.width
    
    @property
    def height(self):
        return self.template.height
    
    @property
    def platforms(self):
        if self._platforms is None:
            self._create_platforms()
        return self._platforms
    
    @property
    def enemies(self):
        if self._enemies is None:
            self._create_enemies()
        return self._enemies
    
    @property
    def chests(self):
        if self._chests is None:
            self._create_chests()
        return self._chests
    
    @property
    def health_pickups(self):
        if self._health_pickups is None:
            self._create_health_pickups()
        return self._health_pickups
    
    @property
    def doors(self):
        if self._doors is None:
            self._create_doors()
        return self._doors
    
    @property
    def background(self):
        if self._background is None:
            self._load_background()
        return self._background
    
    def _create_platforms(self):
        """Create platform sprites from template data"""
        self._platforms = pygame.sprite.Group()
        
        # Load platform texture
        textures = self._get_textures()
        platform_texture = textures.get('platform')
        
        for platform_data in self.template.platform_data:
            platform = Platform(
                platform_data['x'], 
                platform_data['y'], 
                platform_data['width'], 
                platform_data['height']
            )
            
            # Apply texture if available
            if platform_texture and os.path.exists(platform_texture):
                try:
                    texture_surface = pygame.image.load(platform_texture)
                    platform.image = pygame.transform.scale(texture_surface, (platform_data['width'], platform_data['height']))
                except:
                    pass  # Use default if texture loading fails
            
            self._platforms.add(platform)
    
    def _create_enemies(self):
        """Create enemy sprites from template data"""
        self._enemies = pygame.sprite.Group()
        
        # Load enemy texture
        textures = self._get_textures()
        enemy_texture = textures.get('enemy')
        boss_texture = textures.get('boss')
        
        for enemy_data in self.template.enemy_data:
            if enemy_data['enemy_type'] == 'boss':
                enemy = Enemy(enemy_data['x'], enemy_data['y'], is_boss=True)
                if boss_texture and os.path.exists(boss_texture):
                    try:
                        texture_surface = pygame.image.load(boss_texture)
                        enemy.image = pygame.transform.scale(texture_surface, (80, 80))
                    except:
                        pass
            else:
                enemy = Enemy(enemy_data['x'], enemy_data['y'])
                if enemy_texture and os.path.exists(enemy_texture):
                    try:
                        texture_surface = pygame.image.load(enemy_texture)
                        enemy.image = pygame.transform.scale(texture_surface, (40, 40))
                    except:
                        pass
            
            self._enemies.add(enemy)
    
    def _create_chests(self):
        """Create chest sprites from template data"""
        self._chests = pygame.sprite.Group()
        
        for chest_data in self.template.chest_data:
            chest = LootChest(chest_data['x'], chest_data['y'])
            self._chests.add(chest)
    
    def _create_health_pickups(self):
        """Create health pickup sprites from template data"""
        self._health_pickups = pygame.sprite.Group()
        
        for health_data in self.template.health_pickup_data:
            health_pickup = HealthPickup(health_data['x'], health_data['y'])
            self._health_pickups.add(health_pickup)
    
    def _create_doors(self):
        """Create door sprites from template data"""
        self._doors = pygame.sprite.Group()
        
        for door_data in self.template.door_data:
            door = Door(door_data['x'], door_data['y'])
            self._doors.add(door)
    
    def _load_background(self):
        """Load background texture"""
        textures = self._get_textures()
        background_texture = textures.get('background')
        
        if background_texture and os.path.exists(background_texture):
            try:
                self._background = pygame.image.load(background_texture)
                self._background = pygame.transform.scale(self._background, (self.width, self.height))
            except:
                self._background = None
        else:
            self._background = None
    
    def _get_textures(self):
        """Get textures for this level (cached)"""
        if self._textures is None:
            if self.game_manager:
                self._textures = self.game_manager.get_textures(self.level_num)
            else:
                self._textures = {}
        return self._textures
    
    def create_level(self, level_num=None, is_boss_room=None):
        """Create level components (for compatibility with existing code)"""
        return (
            self.platforms,
            self.enemies, 
            self.chests,
            self.health_pickups,
            self.doors,
            self.background
        )


class LevelFactory:
    """Ultra-fast level factory with aggressive caching"""
    
    def __init__(self):
        self.template_cache = {}
        self.level_cache = {}
        print("⚡ Level Factory initialized with ultra-fast caching")
    
    def get_level_template(self, level_num, is_boss_room=False):
        """Get level template (ultra-fast, no sprite creation)"""
        cache_key = f"{level_num}_{is_boss_room}"
        
        if cache_key not in self.template_cache:
            self.template_cache[cache_key] = LevelTemplate(level_num, is_boss_room)
        
        return self.template_cache[cache_key]
    
    def create_level(self, level_num, is_boss_room=False, game_manager=None):
        """Create optimized level instance"""
        cache_key = f"{level_num}_{is_boss_room}"
        
        # Always create fresh level instances to avoid state issues
        # but use cached templates for fast initialization
        template = self.get_level_template(level_num, is_boss_room)
        level = OptimizedLevel(template, game_manager)
        
        return level


# Global level factory instance
level_factory = LevelFactory()


def get_level_factory():
    """Get the global level factory instance"""
    return level_factory


if __name__ == "__main__":
    # Test the level factory
    import time
    
    factory = get_level_factory()
    
    print("Testing Level Factory Performance:")
    
    # Test template creation (should be very fast)
    start = time.time()
    for i in range(1, 4):
        for is_boss in [False, True]:
            template = factory.get_level_template(i, is_boss)
    template_time = time.time() - start
    print(f"Template creation: {template_time:.3f}s")
    
    # Test level creation (should be fast)
    start = time.time()
    for i in range(1, 4):
        for is_boss in [False, True]:
            level = factory.create_level(i, is_boss)
    level_time = time.time() - start
    print(f"Level creation: {level_time:.3f}s")
    
    print("✅ Level Factory test complete!")
