"""
Optimized Main Game Launcher

This version implements all performance optimizations:
- Lazy loading of levels (no preloading during startup)
- Background texture loading
- Minimal initialization overhead
- Fast level switching
"""

import pygame
import sys
import time
from pygame.locals import *
from settings import *
from sprites import Player, Platform, Enemy, LootChest, Camera, HealthPickup
from game_manager import get_game_manager

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Initialize pygame
pygame.init()

# Set up the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# Load fonts
font = pygame.font.SysFont(None, 36)

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2


class OptimizedGame:
    """Optimized game class with minimal startup overhead"""
    
    def __init__(self):
        print("🚀 Starting optimized game...")
        start_time = time.time()
        
        self.state = STATE_MENU
        self.current_level = 1
        
        # Get game manager (textures load in background)
        self.game_manager = get_game_manager()
        
        # Initialize with minimal overhead - no level preloading!
        self.level = None
        self.player = None
        self.platforms = None
        self.enemies = None
        self.chests = None
        self.health_pickups = None
        self.doors = None
        self.background = None
        self.camera = None
        
        # UI elements
        self.popup_font = pygame.font.SysFont(None, 24)
        self.popups = []
        
        # Game state
        self.is_boss_room = False
        self.attack_effect = None
        self.attack_effect_timer = 0
        self.nearby_chest = None
        self.nearby_door = None
        
        # Performance tracking
        self.level_load_times = {}
        
        init_time = time.time() - start_time
        print(f"✅ Game initialized in {init_time:.3f}s (ultra-fast!)")
    
    def reset_game(self):
        """Reset game to level 1"""
        self.current_level = 1
        self.state = STATE_PLAYING
        self.load_level(self.current_level)
        
        # Reset game state
        self.attack_effect = None
        self.attack_effect_timer = 0
        self.nearby_chest = None
        self.nearby_door = None
    
    def load_level(self, level_num, is_boss_room=False):
        """Load level with optimized caching (ultra-fast)"""
        start_time = time.time()
        print(f"⚡ Loading level {level_num} (boss: {is_boss_room})...")
        
        # Create player
        self.player = Player(100, 300)
        
        # Get level from optimized cache (instant after first load)
        self.level = self.game_manager.get_level(level_num, is_boss_room)
        
        # Get level components (lazy loading - only creates sprites when accessed)
        self.platforms, self.enemies, self.chests, self.health_pickups, self.doors, self.background = self.level.create_level(level_num, is_boss_room)
        
        # Set state
        self.is_boss_room = is_boss_room
        
        # Create camera
        self.camera = Camera(self.level.width, self.level.height)
        
        # Track performance
        load_time = time.time() - start_time
        self.level_load_times[f'level_{level_num}_{is_boss_room}'] = load_time
        print(f"✅ Level {level_num} loaded in {load_time:.3f}s")
    
    def handle_events(self):
        """Handle game events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if self.state == STATE_PLAYING:
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        self.player.jump()
                    if event.key == K_x:  # Melee attack
                        self.attack_effect, enemies_hit = self.player.melee_attack(self.enemies)
                        if self.attack_effect:
                            self.attack_effect_timer = 10
                    if event.key == K_c:  # Ranged attack
                        if self.player.ranged_attack():
                            pass
            
            elif self.state == STATE_GAME_OVER:
                if event.type == KEYDOWN and event.key == K_r:
                    self.reset_game()
            
            elif self.state == STATE_MENU:
                if event.type == KEYDOWN and event.key == K_RETURN:
                    self.reset_game()
    
    def update(self):
        """Update game state"""
        if self.state == STATE_PLAYING and self.level is not None:
            # Handle movement
            keys = pygame.key.get_pressed()
            self.player.vel_x = 0
            
            if keys[K_LEFT]:
                self.player.vel_x = -self.player.speed
            if keys[K_RIGHT]:
                self.player.vel_x = self.player.speed
            
            # Update player
            self.player.update(self.platforms)
            
            # Update camera
            self.camera.update(self.player)
            
            # Update enemies
            self.enemies.update()
            
            # Update attack effect timer
            if self.attack_effect_timer > 0:
                self.attack_effect_timer -= 1
                if self.attack_effect_timer <= 0:
                    self.attack_effect = None
            
            # Check collisions
            self._check_collisions()
            
            # Check game over conditions
            if self.player.health <= 0:
                self.state = STATE_GAME_OVER
            
            # Check level completion
            if len(self.enemies) == 0 and not self.is_boss_room:
                self.progress_to_next_level()
    
    def _check_collisions(self):
        """Check all game collisions"""
        # Enemy collisions
        enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for enemy in enemy_hits:
            if not self.player.invulnerable:
                self.player.take_damage(enemy.damage)
        
        # Chest proximity
        self.nearby_chest = None
        for chest in self.chests:
            if abs(self.player.rect.centerx - chest.rect.centerx) < 60 and abs(self.player.rect.centery - chest.rect.centery) < 60:
                self.nearby_chest = chest
                keys = pygame.key.get_pressed()
                if keys[K_DOWN] and not chest.opened:
                    chest.open()
                    self.player.score += chest.value
                break
        
        # Door proximity
        self.nearby_door = None
        for door in self.doors:
            if abs(self.player.rect.centerx - door.rect.centerx) < 60 and abs(self.player.rect.centery - door.rect.centery) < 60:
                if len(self.enemies) == 0:
                    door.activated = True
                    self.nearby_door = door
                    keys = pygame.key.get_pressed()
                    if keys[K_DOWN]:
                        self.progress_to_next_level()
                break
        
        # Health pickup collisions
        health_hits = pygame.sprite.spritecollide(self.player, self.health_pickups, True)
        for health_pickup in health_hits:
            self.player.heal(health_pickup.health_amount)
    
    def progress_to_next_level(self):
        """Progress to next level"""
        if self.current_level < 3:
            self.current_level += 1
            self.load_level(self.current_level)
        elif self.current_level == 3 and not self.is_boss_room:
            # Go to boss room
            self.load_level(3, is_boss_room=True)
        else:
            # Victory!
            self.state = STATE_GAME_OVER
    
    def draw(self):
        """Draw game"""
        screen.fill(BLACK)
        
        if self.state == STATE_MENU:
            # Menu screen
            title_text = font.render("AI GAME - OPTIMIZED", True, WHITE)
            start_text = font.render("Press ENTER to start", True, WHITE)
            screen.blit(title_text, (WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 50))
            screen.blit(start_text, (WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 2))
            
            # Show performance stats
            stats = self.game_manager.get_performance_stats()
            status_text = f"Textures: {'Ready' if stats['textures_ready'] else 'Loading...'}"
            status_surface = self.popup_font.render(status_text, True, GREEN if stats['textures_ready'] else YELLOW)
            screen.blit(status_surface, (10, WINDOW_HEIGHT - 30))
        
        elif self.state == STATE_PLAYING and self.level is not None:
            # Draw background
            if self.background:
                screen.blit(self.background, self.camera.apply_to_rect(pygame.Rect(0, 0, self.level.width, self.level.height)))
            
            # Draw game objects
            for platform in self.platforms:
                screen.blit(platform.image, self.camera.apply(platform))
            
            for enemy in self.enemies:
                screen.blit(enemy.image, self.camera.apply(enemy))
            
            for chest in self.chests:
                screen.blit(chest.image, self.camera.apply(chest))
            
            for health_pickup in self.health_pickups:
                screen.blit(health_pickup.image, self.camera.apply(health_pickup))
            
            for door in self.doors:
                screen.blit(door.image, self.camera.apply(door))
            
            # Draw player
            screen.blit(self.player.image, self.camera.apply(self.player))
            
            # Draw attack effect
            if self.attack_effect:
                screen.blit(self.attack_effect.image, self.camera.apply(self.attack_effect))
            
            # Draw UI
            self._draw_ui()
        
        elif self.state == STATE_GAME_OVER:
            # Game over screen
            if self.player and self.player.health <= 0:
                game_over_text = font.render("GAME OVER", True, RED)
                restart_text = font.render("Press R to restart", True, WHITE)
                screen.blit(game_over_text, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 50))
                screen.blit(restart_text, (WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 2 + 10))
            else:
                victory_text = font.render("VICTORY!", True, GREEN)
                final_score_text = font.render(f"Final Score: {self.player.score if self.player else 0}", True, WHITE)
                restart_text = font.render("Press R to Play Again", True, WHITE)
                screen.blit(victory_text, (WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 - 80))
                screen.blit(final_score_text, (WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 2 - 20))
                screen.blit(restart_text, (WINDOW_WIDTH // 2 - 140, WINDOW_HEIGHT // 2 + 40))
        
        pygame.display.update()
    
    def _draw_ui(self):
        """Draw game UI"""
        if not self.player:
            return
        
        # Health bar
        health_bar_width = 200
        health_bar_height = 20
        health_bar_border = pygame.Rect(10, 10, health_bar_width, health_bar_height)
        health_bar_fill = pygame.Rect(10, 10, int(health_bar_width * (self.player.health / self.player.max_health)), health_bar_height)
        
        pygame.draw.rect(screen, RED, health_bar_border, 2)
        pygame.draw.rect(screen, GREEN, health_bar_fill)
        
        # Health text
        health_text = font.render(f"Health: {int(self.player.health)}/{self.player.max_health}", True, WHITE)
        screen.blit(health_text, (10, 35))
        
        # Score text
        score_text = font.render(f"Score: {self.player.score}", True, WHITE)
        screen.blit(score_text, (10, 70))
        
        # Level text
        level_text = font.render(f"Level: {self.current_level} {'(Boss)' if self.is_boss_room else ''}", True, WHITE)
        screen.blit(level_text, (10, 105))
        
        # Interaction prompts
        if self.nearby_chest and not self.nearby_chest.opened:
            popup_text = self.popup_font.render("Press DOWN to open chest!", True, WHITE)
            chest_pos = self.camera.apply(self.nearby_chest)
            screen.blit(popup_text, (chest_pos.x - 50, chest_pos.y - 30))
        
        if self.nearby_door and self.nearby_door.activated:
            popup_text = self.popup_font.render("Press DOWN to enter door!", True, WHITE)
            door_pos = self.camera.apply(self.nearby_door)
            screen.blit(popup_text, (door_pos.x - 50, door_pos.y - 30))


def main():
    """Main game loop with performance monitoring"""
    print("🎮 Starting AI Game with Performance Optimizations...")
    
    # Track total startup time
    total_start = time.time()
    
    # Create optimized game
    game = OptimizedGame()
    
    total_startup = time.time() - total_start
    print(f"🚀 Total game startup: {total_startup:.3f}s")
    
    # Main game loop
    frame_count = 0
    fps_timer = time.time()
    
    while True:
        game.handle_events()
        game.update()
        game.draw()
        clock.tick(FPS)
        
        # Performance monitoring
        frame_count += 1
        if frame_count % 300 == 0:  # Every 5 seconds at 60 FPS
            current_time = time.time()
            actual_fps = 300 / (current_time - fps_timer)
            print(f"📊 Performance: {actual_fps:.1f} FPS, Memory: {game.game_manager.get_performance_stats()}")
            fps_timer = current_time


if __name__ == "__main__":
    main()
