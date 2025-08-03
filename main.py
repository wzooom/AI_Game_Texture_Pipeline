import pygame
import sys
import random
from pygame.locals import *
from settings import *
from sprites import Player, Platform, Enemy, LootChest, Camera, HealthPickup
from level import Level

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

class Game:
    def __init__(self):
        self.state = STATE_MENU
        
        # Current level number
        self.current_level = 1
        
        # Initialize level with current level number
        self.level = Level(self.current_level)
        
        # Create smaller font for popups
        self.popup_font = pygame.font.SysFont(None, 24)
        
        # Background texture
        self.background = None
        
        # Popup messages list (text, position, timer)
        self.popups = []
        
        self.reset_game()
    
    def reset_game(self):
        # Reset to level 1
        self.current_level = 1
        self.load_level(self.current_level)
        
        # Game variables
        self.state = STATE_PLAYING
        self.attack_effect = None
        self.attack_effect_timer = 0
        self.nearby_chest = None  # Track the chest that player is near
        self.nearby_door = None   # Track the door that player is near
    
    def load_level(self, level_num, is_boss_room=False):
        """Load a specific level or boss room"""
        # Create player with position based on whether it's a regular level or boss room
        if is_boss_room:
            # Position player at the start of the boss room
            self.player = Player(100, 300)
        else:
            # Position player at the start of a regular level
            self.player = Player(100, 300)
        
        # Create a new level instance with the correct level number and room type
        self.level = Level(level_num, is_boss_room)
        
        # Create level with textures
        if is_boss_room:
            self.platforms, self.enemies, self.chests, self.health_pickups, self.doors, self.background = self.level.create_level(level_num, is_boss_room)
        else:
            self.platforms, self.enemies, self.chests, self.health_pickups, self.doors, self.background = self.level.create_level(level_num)
        
        # Set boss room flag
        self.is_boss_room = is_boss_room
        
        # Create camera
        self.camera = Camera(self.level.width, self.level.height)
    
    def handle_events(self):
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
                            self.attack_effect_timer = 10  # Show attack effect for 10 frames
                    if event.key == K_c:  # Ranged attack
                        if self.player.ranged_attack():
                            pass  # Could add sound effect here
            
            elif self.state == STATE_GAME_OVER:
                if event.type == KEYDOWN and event.key == K_r:
                    self.reset_game()
            
            elif self.state == STATE_MENU:
                if event.type == KEYDOWN and event.key == K_RETURN:
                    self.state = STATE_PLAYING
    
    def update(self):
        if self.state == STATE_PLAYING:
            # Get key states
            keys = pygame.key.get_pressed()
            self.player.vel_x = 0
            
            if keys[K_LEFT]:
                self.player.vel_x = -PLAYER_SPEED
                self.player.facing_right = False
            if keys[K_RIGHT]:
                self.player.vel_x = PLAYER_SPEED
                self.player.facing_right = True
            
            # Update game objects
            self.player.update(self.platforms, self.enemies)
            
            # Update projectiles and check for collisions with enemies
            for projectile in list(self.player.projectiles):
                # Check if projectile hits any enemy
                for enemy in list(self.enemies):
                    if projectile.rect.colliderect(enemy.rect):
                        if enemy.take_damage(projectile.damage):
                            self.player.score += enemy.score_value
                        projectile.kill()
                        break
                        
                # Remove projectiles that go off-screen
                if (projectile.rect.right < 0 or projectile.rect.left > self.level.width or
                    projectile.rect.bottom < 0 or projectile.rect.top > self.level.height):
                    projectile.kill()
            
            self.enemies.update(self.player)
            
            # Update health pickups (bobbing animation)
            for pickup in self.health_pickups:
                pickup.update()
            
            # Check for health pickup collisions
            pickup_collisions = pygame.sprite.spritecollide(self.player, self.health_pickups, False)
            for pickup in pickup_collisions:
                health_gained = pickup.collect()
                if health_gained > 0:
                    self.player.health = min(self.player.max_health, self.player.health + health_gained)
                    # Optional: Show health pickup popup
                    print(f"Health +{health_gained}")
            
            # Update camera to follow player
            self.camera.update(self.player)
            
            # Check for nearby chests and chest interactions
            self.nearby_chest = None
            for chest in self.chests:
                # Check if player is near any chest
                if chest.is_player_nearby(self.player):
                    self.nearby_chest = chest
                
                # Open chest if player presses down key while colliding with chest
                if self.player.rect.colliderect(chest.rect) and keys[K_DOWN]:
                    loot = chest.open()
                    if loot > 0:
                        self.player.score += loot
            
            # Check for nearby doors and door interactions
            self.nearby_door = None
            for door in self.doors:
                # Check if player is near any door
                if door.is_player_nearby(self.player):
                    self.nearby_door = door
                
                # Enter door if player presses down key while near an activated door
                if door.activated and door.is_player_nearby(self.player) and keys[K_DOWN]:
                    # Transition to boss room if in regular level
                    if not hasattr(self, 'is_boss_room') or not self.is_boss_room:
                        self.add_popup("Entering boss room!", self.player.rect.centerx, self.player.rect.top - 30)
                        self.load_level(self.current_level, is_boss_room=True)
                    else:
                        # If in boss room and all enemies defeated, proceed to next level
                        if len(self.enemies) == 0:
                            self.current_level += 1
                            if self.current_level > 3:  # Assuming 3 levels total
                                self.state = STATE_GAME_OVER  # Game completed
                                self.add_popup("Game Completed!", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50)
                            else:
                                self.load_level(self.current_level)
                                self.add_popup(f"Level {self.current_level}!", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            
            # Check if all enemies are defeated to progress to next level
            if len(self.enemies) == 0:
                self.progress_to_next_level()
    
    def progress_to_next_level(self):
        """Progress to the next level or win the game"""
        if self.current_level < 3:  # We have 3 levels total
            self.current_level += 1
            # Keep player's score when progressing
            current_score = self.player.score
            # Load the next level
            self.load_level(self.current_level)
            # Restore player's score
            self.player.score = current_score
            # Show level transition message
            print(f"Level {self.current_level} loaded!")
        else:
            # Player has completed all levels
            self.state = STATE_GAME_OVER
            print("Congratulations! You've completed all levels!")
            # Could add a victory screen here
            
            # Reduce attack effect timer
            if self.attack_effect_timer > 0:
                self.attack_effect_timer -= 1
            else:
                self.attack_effect = None
            
            # Check for door activation (unlock when all enemies defeated)
            for door in self.doors:
                if len(self.enemies) == 0 and not door.activated:
                    door.activate()
                    self.add_popup("Door unlocked!", self.player.rect.centerx, self.player.rect.top - 30)
            
            # Check if player is dead
            if self.player.health <= 0:
                self.state = STATE_GAME_OVER
    
    def draw(self):
        # Clear screen
        screen.fill(BLACK)
        
        if self.state == STATE_MENU:
            # Draw menu
            title_text = font.render("2D PLATFORMER GAME", True, WHITE)
            start_text = font.render("Press ENTER to Start", True, WHITE)
            screen.blit(title_text, (WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 50))
            screen.blit(start_text, (WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 2 + 10))
        
        elif self.state == STATE_PLAYING or self.state == STATE_GAME_OVER:
            # Draw background if available
            if self.background:
                # Scale background to fit screen plus extra for camera movement
                bg_width, bg_height = WINDOW_WIDTH * 1.5, WINDOW_HEIGHT * 1.5
                scaled_bg = pygame.transform.scale(self.background, (bg_width, bg_height))
                
                # Calculate parallax scrolling effect (background moves slower than foreground)
                # Using a smaller factor makes the background move less with the camera
                bg_x = self.camera.camera.x * 0.1  # Reduced parallax factor
                bg_y = self.camera.camera.y * 0.1  # Reduced parallax factor
                
                # Draw background with parallax offset, centered on screen
                # The extra width/height ensures we never see the edge of the background
                offset_x = -bg_x - (bg_width - WINDOW_WIDTH) // 2
                offset_y = -bg_y - (bg_height - WINDOW_HEIGHT) // 2
                screen.blit(scaled_bg, (offset_x, offset_y))
            else:
                # Fallback to solid color
                screen.fill(BLACK)
            # Draw platforms with camera offset
            for platform in self.platforms:
                screen.blit(platform.image, self.camera.apply(platform))
            
            # Draw enemies with camera offset
            for enemy in self.enemies:
                # Draw enemy sprite
                enemy_pos = self.camera.apply(enemy)
                screen.blit(enemy.image, enemy_pos)
                
                # Draw enemy health bar above enemy
                health_percent = enemy.health / enemy.max_health
                bar_width = enemy.rect.width
                bar_height = 5
                
                # Health bar background (red)
                health_bar_bg = pygame.Rect(
                    enemy_pos.x,
                    enemy_pos.y - 10,
                    bar_width,
                    bar_height
                )
                
                # Health bar fill (green)
                health_bar_fill = pygame.Rect(
                    enemy_pos.x,
                    enemy_pos.y - 10,
                    int(bar_width * health_percent),
                    bar_height
                )
                
                pygame.draw.rect(screen, RED, health_bar_bg)
                pygame.draw.rect(screen, GREEN, health_bar_fill)
            
            # Draw chests with camera offset
            for chest in self.chests:
                screen.blit(chest.image, self.camera.apply(chest))
                
            # Draw health pickups with camera offset
            for health_pickup in self.health_pickups:
                screen.blit(health_pickup.image, self.camera.apply(health_pickup))
                
            # Draw doors with camera offset
            for door in self.doors:
                screen.blit(door.image, self.camera.apply(door))
                
            # Draw projectiles with camera offset
            for projectile in self.player.projectiles:
                screen.blit(projectile.image, self.camera.apply(projectile))
            
            # Draw player with camera offset
            screen.blit(self.player.image, self.camera.apply(self.player))
            
            # Draw attack effect if active
            if self.attack_effect and self.attack_effect_timer > 0:
                # Create dynamic attack animation based on timer
                progress = 1.0 - (self.attack_effect_timer / 10.0)  # Progress from 0 to 1
                
                # Create multiple attack slashes for better visual effect
                for i in range(3):
                    # Calculate offset for each slash
                    offset_x = i * 8 * progress
                    offset_y = i * 4 * progress
                    
                    # Create attack surface with fading effect
                    attack_surface = pygame.Surface((self.attack_effect.width, self.attack_effect.height))
                    
                    # Color changes from yellow to red over time
                    red_component = min(255, 150 + int(105 * progress))
                    green_component = max(100, 255 - int(155 * progress))
                    attack_color = (red_component, green_component, 0)
                    
                    attack_surface.fill(attack_color)
                    
                    # Alpha decreases over time and with each slash layer
                    alpha = max(30, int(150 * (1 - progress) * (1 - i * 0.3)))
                    attack_surface.set_alpha(alpha)
                    
                    # Position with camera offset and animation offset
                    attack_rect = attack_surface.get_rect()
                    attack_rect.x = self.attack_effect.x + self.camera.camera.x + offset_x
                    attack_rect.y = self.attack_effect.y + self.camera.camera.y + offset_y
                    
                    screen.blit(attack_surface, attack_rect)
                
                # Add impact particles for extra effect
                if self.attack_effect_timer > 7:  # Only show particles in first few frames
                    for i in range(5):
                        particle_x = self.attack_effect.x + self.camera.camera.x + (i * 10) - 20
                        particle_y = self.attack_effect.y + self.camera.camera.y + (i * 5) - 10
                        particle_size = max(2, 8 - i)
                        pygame.draw.circle(screen, (255, 255, 100), (int(particle_x), int(particle_y)), particle_size)
                
            # Draw popup if player is near a chest
            if self.nearby_chest:
                # Create popup background
                popup_width = 200
                popup_height = 40
                popup_surface = pygame.Surface((popup_width, popup_height))
                popup_surface.fill(GRAY)
                popup_surface.set_alpha(220)  # Semi-transparent
                
                # Create popup text
                popup_text = self.popup_font.render("Press DOWN to open chest!", True, WHITE)
                
                # Position popup above the chest
                chest_pos = self.camera.apply(self.nearby_chest)
                popup_x = chest_pos.x - (popup_width - self.nearby_chest.rect.width) // 2
                popup_y = chest_pos.y - popup_height - 10
                
                # Draw popup
                screen.blit(popup_surface, (popup_x, popup_y))
                screen.blit(popup_text, (popup_x + 10, popup_y + (popup_height - popup_text.get_height()) // 2))
            
            # Draw popup if player is near an activated door
            if self.nearby_door and self.nearby_door.activated:
                # Create popup background
                popup_width = 200
                popup_height = 40
                popup_surface = pygame.Surface((popup_width, popup_height))
                popup_surface.fill(BLUE)
                popup_surface.set_alpha(220)  # Semi-transparent
                
                # Create popup text
                popup_text = self.popup_font.render("Press DOWN to enter door!", True, WHITE)
                
                # Position popup above the door
                door_pos = self.camera.apply(self.nearby_door)
                popup_x = door_pos.x - (popup_width - self.nearby_door.rect.width) // 2
                popup_y = door_pos.y - popup_height - 10
                
                # Draw popup
                screen.blit(popup_surface, (popup_x, popup_y))
                screen.blit(popup_text, (popup_x + 10, popup_y + (popup_height - popup_text.get_height()) // 2))
            
            # Draw HUD (not affected by camera)
            # Player health bar
            health_bar_width = 200
            health_bar_height = 20
            health_bar_border = pygame.Rect(10, 10, health_bar_width, health_bar_height)
            health_bar_fill = pygame.Rect(10, 10, int(health_bar_width * (self.player.health / self.player.max_health)), health_bar_height)
            
            # Draw health bar
            pygame.draw.rect(screen, RED, health_bar_border, 2)  # Border
            pygame.draw.rect(screen, GREEN, health_bar_fill)    # Fill
            
            # Health text
            health_text = font.render(f"Health: {int(self.player.health)}/{self.player.max_health}", True, WHITE)
            screen.blit(health_text, (10, 35))
            
            # Score text
            score_text = font.render(f"Score: {self.player.score}", True, WHITE)
            screen.blit(score_text, (10, 70))
            
            # Draw game over screen
            if self.state == STATE_GAME_OVER:
                if self.player.health <= 0:
                    # Game over due to death
                    game_over_text = font.render("GAME OVER", True, RED)
                    restart_text = font.render("Press R to restart", True, WHITE)
                    screen.blit(game_over_text, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 50))
                    screen.blit(restart_text, (WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 2 + 10))
                else:
                    # Victory screen
                    victory_text = font.render("VICTORY!", True, GREEN)
                    final_score_text = font.render(f"Final Score: {self.player.score}", True, WHITE)
                    restart_text = font.render("Press R to Play Again", True, WHITE)
                    screen.blit(victory_text, (WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 - 80))
                    screen.blit(final_score_text, (WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT // 2 - 20))
                    screen.blit(restart_text, (WINDOW_WIDTH // 2 - 140, WINDOW_HEIGHT // 2 + 40))
        
        # Update display
        pygame.display.update()

def main():
    game = Game()
    
    # Main game loop
    while True:
        game.handle_events()
        game.update()
        game.draw()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
