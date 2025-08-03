import pygame
import random
import math
from settings import *

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, damage=15):
        super().__init__()
        self.image = pygame.Surface((10, 5))
        self.image.fill(BLUE)  # Blue projectile
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = direction  # 1 for right, -1 for left
        self.speed = 10
        self.damage = damage
        self.lifetime = 60  # Projectile disappears after 60 frames (1 second)
    
    def update(self):
        self.rect.x += self.speed * self.direction
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 50))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.jumping = False
        self.on_ground = False
        self.score = 0
        self.facing_right = True
        
        # Attack attributes
        self.melee_cooldown = 0
        self.ranged_cooldown = 0
        self.melee_damage = 25
        self.ranged_damage = 15
        self.projectiles = pygame.sprite.Group()
        
        # Health attributes
        self.max_health = 100
        self.health = self.max_health
        self.health_regen = 0.01
        self.invulnerable = 0  # Invulnerability frames
        self.damage_flash = 0   # Visual feedback when taking damage
        
        # Visual attributes
        self.original_image = self.image  # Store original image for flipping
        self.flash_image = None  # Will store red-tinted image for damage feedback
    
    def set_texture(self, texture):
        """Set a texture for the player"""
        # Scale the texture to match player size
        self.original_image = pygame.transform.scale(texture, (30, 50))
        self.image = self.original_image
        # Update the rect in case the size changed
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))

    def update(self, platforms, enemies):
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Move horizontally
        self.rect.x += self.vel_x
        
        # Check for collisions with platforms (horizontal)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = platform.rect.right
        
        # Move vertically
        self.rect.y += self.vel_y
        self.on_ground = False
        
        # Check for collisions with platforms (vertical)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling
                    self.rect.bottom = platform.rect.top
                    self.on_ground = True
                    self.vel_y = 0
                elif self.vel_y < 0:  # Jumping
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
        
        # Reduce attack cooldowns
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
            
        if self.ranged_cooldown > 0:
            self.ranged_cooldown -= 1
            
        # Update projectiles
        self.projectiles.update()
        
        # For backward compatibility
        if hasattr(self, 'attack_cooldown') and self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Reduce invulnerability frames
        if self.invulnerable > 0:
            self.invulnerable -= 1
            
        # Handle damage flash effect
        if self.damage_flash > 0:
            self.damage_flash -= 1
            # Switch back to normal image when flash ends
            if self.damage_flash == 0 and self.flash_image:
                self.image = self.original_image if self.facing_right else pygame.transform.flip(self.original_image, True, False)
        
        # Health regeneration when not recently damaged
        if self.invulnerable <= 0 and self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.health_regen)
    
    def jump(self):
        if self.on_ground:
            self.vel_y = PLAYER_JUMP_STRENGTH
            self.on_ground = False
    
    def melee_attack(self, enemies):
        """Perform a melee attack that hits enemies in close range"""
        if self.melee_cooldown == 0:
            self.melee_cooldown = 30  # Half a second cooldown
            
            # Create attack area that includes player area and extends in facing direction
            attack_width = 60  # Wider attack area
            attack_height = self.rect.height + 20  # Slightly taller
            
            if self.facing_right:
                # Attack area starts from player center and extends right
                attack_x = self.rect.centerx - 20  # Include part of player area
                attack_rect = pygame.Rect(attack_x, self.rect.y - 10, attack_width, attack_height)
            else:
                # Attack area extends left from player center
                attack_x = self.rect.centerx - attack_width + 20  # Include part of player area
                attack_rect = pygame.Rect(attack_x, self.rect.y - 10, attack_width, attack_height)
            
            enemies_hit = 0
            for enemy in enemies:
                # Check both attack rectangle collision AND direct overlap with player
                if attack_rect.colliderect(enemy.rect) or self.rect.colliderect(enemy.rect):
                    if enemy.take_damage(self.melee_damage):
                        self.score += enemy.score_value  # Score based on enemy type
                        enemies_hit += 1
                    else:
                        enemies_hit += 1
            
            return attack_rect, enemies_hit
        return None, 0

    def ranged_attack(self):
        """Fire a projectile in the direction the player is facing"""
        if self.ranged_cooldown == 0:
            self.ranged_cooldown = 45  # 3/4 second cooldown
            
            # Create projectile at the player's position
            direction = 1 if self.facing_right else -1
            x_pos = self.rect.right if self.facing_right else self.rect.left
            projectile = Projectile(x_pos, self.rect.centery, direction, self.ranged_damage)
            self.projectiles.add(projectile)
            
            return True
        return False

    def attack(self, enemies):
        """Legacy attack method for backward compatibility"""
        return self.melee_attack(enemies)

    def take_damage(self, amount):
        if self.invulnerable <= 0:
            self.health -= amount
            self.invulnerable = 60  # 1 second of invulnerability
            self.damage_flash = 10  # Flash red for 10 frames
            
            # Create damage flash effect (red tint)
            if not self.flash_image and self.original_image:
                self.flash_image = self.original_image.copy()
                red_overlay = pygame.Surface(self.flash_image.get_size(), pygame.SRCALPHA)
                red_overlay.fill((255, 0, 0, 128))  # Semi-transparent red
                self.flash_image.blit(red_overlay, (0, 0))
            
            # Apply the flash image
            if self.flash_image:
                self.image = self.flash_image if self.facing_right else pygame.transform.flip(self.flash_image, True, False)
            
            if self.health < 0:
                self.health = 0
            
            return True  # Indicate damage was taken
        return False  # No damage was taken

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = width
        self.height = height
    
    def set_texture(self, texture):
        """Set a texture for the platform"""
        # Scale the texture to match platform size
        scaled_texture = pygame.transform.scale(texture, (self.width, self.height))
        self.image = scaled_texture

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, platform=None, enemy_type="normal"):
        super().__init__()
        self.image = pygame.Surface((30, 40))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = ENEMY_SPEED
        
        # Enemy type and level-based stats
        self.enemy_type = enemy_type  # "normal", "strong", "boss"
        
        # Set health based on enemy type
        if enemy_type == "boss":
            self.max_health = 200
            self.attack_damage = 20
            self.score_value = 50
        elif enemy_type == "strong":
            self.max_health = 100
            self.attack_damage = 15
            self.score_value = 20
        else:  # normal
            self.max_health = 50
            self.attack_damage = 10
            self.score_value = 10
            
        self.health = self.max_health
        
        # Movement and combat
        self.platform = platform
        self.direction = 1  # 1 for right, -1 for left
        self.attack_cooldown = 0
        self.attack_range = 50  # Distance at which enemy can attack player
        
        # Visual effects
        self.original_image = self.image  # Store original image for flipping
        self.damage_flash = 0  # Visual feedback when taking damage
        self.flash_image = None  # Will store red-tinted image for damage feedback
    
    def set_texture(self, texture):
        """Set a texture for the enemy"""
        # Scale the texture to match enemy size
        self.original_image = pygame.transform.scale(texture, (30, 40))
        self.image = self.original_image
        # Update the rect in case the size changed
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))

    def melee_attack(self, player):
        """Perform a melee attack against the player if in range"""
        if self.attack_cooldown <= 0:
            # Create attack rectangle in front of enemy based on direction
            attack_width = 30
            attack_rect = pygame.Rect(
                self.rect.x - attack_width if self.direction < 0 else self.rect.right,
                self.rect.y,
                attack_width,
                self.rect.height
            )
            
            # Check if player is within attack range
            if attack_rect.colliderect(player.rect):
                player.take_damage(self.attack_damage)
                self.attack_cooldown = 60  # 1 second cooldown
                return attack_rect
        
        return None
    
    def update(self, player):
        # Basic AI: move back and forth on platform
        if self.platform:
            # Calculate distance to player
            distance_to_player = abs(self.rect.centerx - player.rect.centerx)
            
            # Only move towards player if they're far enough away (maintain minimum distance)
            min_distance = 80  # Minimum distance to maintain from player
            
            if distance_to_player > min_distance:
                # Move towards player but at reduced speed for lag effect
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    # Only move if not at platform edge
                    if self.rect.left > self.platform.rect.left:
                        self.rect.x += (self.vel_x * 0.7) * self.direction  # 70% speed for lag
                else:
                    self.direction = 1
                    # Only move if not at platform edge
                    if self.rect.right < self.platform.rect.right:
                        self.rect.x += (self.vel_x * 0.7) * self.direction  # 70% speed for lag
            else:
                # If too close, back away slightly
                if player.rect.centerx < self.rect.centerx and self.rect.right < self.platform.rect.right:
                    self.direction = 1
                    self.rect.x += (self.vel_x * 0.3)  # Slow backing away
                elif player.rect.centerx > self.rect.centerx and self.rect.left > self.platform.rect.left:
                    self.direction = -1
                    self.rect.x += (self.vel_x * 0.3) * self.direction  # Slow backing away
            
            # Ensure enemy stays on platform
            if self.rect.right >= self.platform.rect.right:
                self.rect.right = self.platform.rect.right
            elif self.rect.left <= self.platform.rect.left:
                self.rect.left = self.platform.rect.left
            
        # Attack player if in range but not too close
        attack_distance = 60  # Slightly larger attack range
        if distance_to_player <= attack_distance and abs(self.rect.y - player.rect.y) < 50:
            self.melee_attack(player)
        
        # Reduce attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Handle damage flash effect
        if self.damage_flash > 0:
            self.damage_flash -= 1
            # Switch back to normal image when flash ends
            if self.damage_flash == 0 and self.flash_image:
                self.image = self.original_image if self.direction > 0 else pygame.transform.flip(self.original_image, True, False)

    def take_damage(self, amount):
        self.health -= amount
        self.damage_flash = 10  # Flash red for 10 frames
        
        # Create damage flash effect (red tint)
        if not self.flash_image and self.original_image:
            self.flash_image = self.original_image.copy()
            red_overlay = pygame.Surface(self.flash_image.get_size(), pygame.SRCALPHA)
            red_overlay.fill((255, 0, 0, 128))  # Semi-transparent red
            self.flash_image.blit(red_overlay, (0, 0))
        
        # Apply the flash image
        if self.flash_image:
            self.image = self.flash_image if self.direction > 0 else pygame.transform.flip(self.flash_image, True, False)
        
        if self.health <= 0:
            self.kill()
            return True
        return False

class HealthPickup(pygame.sprite.Sprite):
    def __init__(self, x, y, health_value=25):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill((0, 255, 0))  # Bright green for health
        
        # Draw a red cross on the health pickup
        pygame.draw.line(self.image, (255, 0, 0), (8, 4), (8, 16), 4)  # Vertical line
        pygame.draw.line(self.image, (255, 0, 0), (4, 10), (16, 10), 4)  # Horizontal line
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health_value = health_value
        self.bob_height = 10  # How high it bobs up and down
        self.bob_speed = 0.05  # Speed of bobbing
        self.bob_offset = 0  # Current offset
        self.original_y = y  # Store original y position
        self.collected = False  # Whether this pickup has been collected
    
    def update(self):
        # Make the health pickup bob up and down
        self.bob_offset += self.bob_speed
        self.rect.y = self.original_y + int(math.sin(self.bob_offset) * self.bob_height)
    
    def collect(self):
        if not self.collected:
            self.collected = True
            self.kill()
            return self.health_value
        return 0

class LootChest(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 30))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.opened = False
        self.loot_value = random.randint(10, 50)
        self.interaction_distance = 70  # Distance at which player can interact with chest
        self.closed_image = self.image  # Store closed chest image
        self.opened_image = None  # Will store opened chest image
    
    def set_texture(self, texture):
        """Set a texture for the chest"""
        # Scale the texture to match chest size
        self.closed_image = pygame.transform.scale(texture, (40, 30))
        self.image = self.closed_image
        
        # Create an opened version with a different color tint
        self.opened_image = self.closed_image.copy()
        # Apply a light gray tint to show it's been opened
        overlay = pygame.Surface((40, 30), pygame.SRCALPHA)
        overlay.fill((200, 200, 200, 128))  # Semi-transparent light gray
        self.opened_image.blit(overlay, (0, 0))

    def is_player_nearby(self, player):
        # Check if player is within interaction distance
        distance = ((self.rect.centerx - player.rect.centerx) ** 2 + 
                   (self.rect.centery - player.rect.centery) ** 2) ** 0.5
        return distance < self.interaction_distance and not self.opened

    def open(self):
        if not self.opened:
            self.opened = True
            # Change to opened image if available
            if self.opened_image:
                self.image = self.opened_image
            return self.loot_value
        return 0

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((50, 80))
        self.image.fill((139, 69, 19))  # Brown door
        
        # Add door details
        pygame.draw.rect(self.image, (101, 67, 33), (5, 5, 40, 70))  # Door panel
        pygame.draw.circle(self.image, (255, 215, 0), (40, 40), 5)  # Gold doorknob
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y - 80  # Position door so bottom is at ground level
        self.activated = False  # Door is locked until all enemies are defeated
        
    def activate(self):
        """Unlock the door when all enemies are defeated"""
        self.activated = True
        # Change door color to indicate it's unlocked
        self.image.fill((160, 120, 40))  # Lighter brown/gold for unlocked door
        pygame.draw.rect(self.image, (120, 90, 30), (5, 5, 40, 70))  # Door panel
        pygame.draw.circle(self.image, (255, 255, 0), (40, 40), 5)  # Brighter doorknob
        
    def is_player_nearby(self, player):
        """Check if player is close enough to interact with the door"""
        return abs(self.rect.centerx - player.rect.centerx) < 50 and \
               abs(self.rect.bottom - player.rect.bottom) < 30

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        
    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)
        
    def update(self, target):
        # Center the camera on the target
        x = -target.rect.x + WINDOW_WIDTH // 2
        y = -target.rect.y + WINDOW_HEIGHT // 2
        
        # Limit scrolling to map size
        x = min(0, x)  # Left side
        y = min(0, y)  # Top side
        x = max(-(self.width - WINDOW_WIDTH), x)  # Right side
        y = max(-(self.height - WINDOW_HEIGHT), y)  # Bottom side
        
        self.camera = pygame.Rect(x, y, self.width, self.height)
