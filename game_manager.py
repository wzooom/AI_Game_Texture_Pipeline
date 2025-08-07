"""
Optimized Game Manager for AI Game

This module provides performance optimizations including:
- Singleton AI pipeline to avoid repeated initialization
- Texture preloading and caching
- Async texture generation
- Level instance reuse
- Resource management
"""

import os
import threading
import time
from ai_pipeline import AITexturePipeline


class GameManager:
    """
    Singleton game manager that handles performance optimizations
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not GameManager._initialized:
            print("🚀 Initializing Game Manager...")
            
            # Singleton AI pipeline - initialize once, use everywhere
            self.ai_pipeline = AITexturePipeline()
            
            # Texture cache and status
            self.texture_cache = {}
            self.textures_loading = False
            self.textures_ready = False
            
            # Level cache
            self.level_cache = {}
            
            # Performance metrics
            self.load_times = {}
            
            # Start background texture loading
            self._start_background_loading()
            
            GameManager._initialized = True
            print("✅ Game Manager initialized")
    
    def _start_background_loading(self):
        """Start loading textures in the background"""
        if not self.textures_ready and not self.textures_loading:
            self.textures_loading = True
            thread = threading.Thread(target=self._load_textures_async, daemon=True)
            thread.start()
            print("🔄 Started background texture loading...")
    
    def _load_textures_async(self):
        """Load textures asynchronously in background"""
        try:
            start_time = time.time()
            
            # Check if textures already exist on disk
            if self._textures_exist_on_disk():
                print("📁 Loading existing textures from disk...")
                self.texture_cache = self._load_existing_textures()
            else:
                print("🎨 Generating new textures...")
                self.texture_cache = self.ai_pipeline.generate_all_textures(num_levels=3)
            
            load_time = time.time() - start_time
            self.load_times['texture_loading'] = load_time
            
            self.textures_ready = True
            self.textures_loading = False
            
            print(f"✅ Textures loaded in {load_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Error loading textures: {e}")
            self.textures_loading = False
            # Create empty cache as fallback
            self.texture_cache = {1: {}, 2: {}, 3: {}}
            self.textures_ready = True
    
    def _textures_exist_on_disk(self):
        """Check if all required textures exist on disk"""
        texture_dir = os.path.join(os.path.dirname(__file__), "assets", "textures")
        
        required_textures = [
            "level_1_background.png", "level_1_platform.png", "level_1_enemy.png",
            "level_2_background.png", "level_2_platform.png", "level_2_enemy.png", 
            "level_3_background.png", "level_3_platform.png", "level_3_enemy.png", "level_3_boss.png"
        ]
        
        for texture in required_textures:
            if not os.path.exists(os.path.join(texture_dir, texture)):
                return False
        
        return True
    
    def _load_existing_textures(self):
        """Load existing texture file paths into cache"""
        texture_dir = os.path.join(os.path.dirname(__file__), "assets", "textures")
        
        texture_cache = {
            1: {
                'background': os.path.join(texture_dir, "level_1_background.png"),
                'platform': os.path.join(texture_dir, "level_1_platform.png"),
                'enemy': os.path.join(texture_dir, "level_1_enemy.png")
            },
            2: {
                'background': os.path.join(texture_dir, "level_2_background.png"),
                'platform': os.path.join(texture_dir, "level_2_platform.png"),
                'enemy': os.path.join(texture_dir, "level_2_enemy.png")
            },
            3: {
                'background': os.path.join(texture_dir, "level_3_background.png"),
                'platform': os.path.join(texture_dir, "level_3_platform.png"),
                'enemy': os.path.join(texture_dir, "level_3_enemy.png"),
                'boss': os.path.join(texture_dir, "level_3_boss.png")
            }
        }
        
        return texture_cache
    
    def get_textures(self, level_num):
        """Get textures for a specific level (blocking if not ready)"""
        # If textures aren't ready yet, show loading message
        if not self.textures_ready:
            if not self.textures_loading:
                self._start_background_loading()
            
            print("⏳ Waiting for textures to load...")
            # Wait for textures to be ready (with timeout)
            timeout = 30  # 30 second timeout
            start_wait = time.time()
            
            while not self.textures_ready and (time.time() - start_wait) < timeout:
                time.sleep(0.1)
            
            if not self.textures_ready:
                print("⚠️ Texture loading timed out, using fallback")
                return {}
        
        return self.texture_cache.get(level_num, {})
    
    def get_ai_pipeline(self):
        """Get the singleton AI pipeline instance"""
        return self.ai_pipeline
    
    def preload_level(self, level_num, is_boss_room=False):
        """Preload a level for faster switching (ultra-fast with level factory)"""
        cache_key = f"{level_num}_{is_boss_room}"
        
        if cache_key not in self.level_cache:
            print(f"⚡ Preloading level {level_num} (boss: {is_boss_room})...")
            
            # Import here to avoid circular imports
            from level_factory import get_level_factory
            
            start_time = time.time()
            factory = get_level_factory()
            level = factory.create_level(level_num, is_boss_room, self)
            load_time = time.time() - start_time
            
            self.level_cache[cache_key] = level
            self.load_times[f'level_{cache_key}'] = load_time
            
            print(f"✅ Level {level_num} preloaded in {load_time:.3f}s")
        
        return self.level_cache[cache_key]
    
    def get_level(self, level_num, is_boss_room=False):
        """Get a level instance (from cache if available)"""
        cache_key = f"{level_num}_{is_boss_room}"
        
        if cache_key in self.level_cache:
            print(f"⚡ Using cached level {level_num}")
            return self.level_cache[cache_key]
        else:
            return self.preload_level(level_num, is_boss_room)
    
    def clear_level_cache(self):
        """Clear level cache to free memory"""
        self.level_cache.clear()
        print("🗑️ Level cache cleared")
    
    def get_performance_stats(self):
        """Get performance statistics"""
        return {
            'textures_ready': self.textures_ready,
            'textures_loading': self.textures_loading,
            'cached_levels': len(self.level_cache),
            'load_times': self.load_times
        }
    
    def regenerate_textures(self):
        """Force regeneration of textures"""
        print("🔄 Regenerating textures...")
        self.textures_ready = False
        self.textures_loading = False
        self.texture_cache.clear()
        self._start_background_loading()


# Global instance
game_manager = GameManager()


def get_game_manager():
    """Get the global game manager instance"""
    return game_manager


if __name__ == "__main__":
    # Test the game manager
    gm = get_game_manager()
    print("Game Manager Test:")
    print(f"Performance stats: {gm.get_performance_stats()}")
    
    # Test texture loading
    textures = gm.get_textures(1)
    print(f"Level 1 textures: {textures}")
    
    # Test level preloading
    level = gm.preload_level(1)
    print(f"Level preloaded: {level}")
    
    print(f"Final stats: {gm.get_performance_stats()}")
