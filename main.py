import pygame, random, math, os, sys
import json

# ================= CONFIG =================
WIDTH, HEIGHT = 900, 520
FPS = 60
PLAYER_FIRE_RATE = 15
BOSS_LEVEL_INTERVAL = 5
BASE_SPEED = 6

# ================= INIT =================
pygame.init()
pygame.mixer.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEO DODGE - Cyber Arena")
CLOCK = pygame.time.Clock()

# ================= COLORS =================
CYBER_BLUE = (0, 200, 255)
CYBER_PINK = (255, 0, 128)
CYBER_PURPLE = (160, 0, 255)
CYBER_GREEN = (0, 255, 128)
CYBER_YELLOW = (255, 220, 0)
CYBER_RED = (255, 40, 40)
NEON_WHITE = (240, 248, 255)
DARK_BG = (10, 12, 18)
UI_BLUE = (20, 60, 120)
PARTICLE_COLORS = [
    (0, 200, 255),    # Blue
    (255, 0, 128),    # Pink
    (160, 0, 255),    # Purple
    (0, 255, 128),    # Green
]

# ================= FONTS =================
FONT_SMALL = pygame.font.SysFont("arial", 16)
FONT = pygame.font.SysFont("arial", 24)
FONT_LARGE = pygame.font.SysFont("arial", 42)
FONT_TITLE = pygame.font.SysFont("arial", 64)

# ================= AUDIO =================
class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        
    def play_sound(self, name, volume=0.3):
        pass
        
    def play_music(self):
        if not self.music_playing:
            self.music_playing = True

audio = AudioManager()

# ================= SAVE SYSTEM =================
SAVE_FILE = "game_save.json"
class SaveData:
    def __init__(self):
        self.high_score = 0
        self.total_kills = 0
        self.total_playtime = 0
        self.unlocked_ships = ["default"]
        self.upgrades = {
            "damage": 0,
            "speed": 0,
            "fire_rate": 0,
            "health": 0,
            "shield": 0
        }
        self.coins = 0
        
    def load(self):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                self.high_score = data.get("high_score", 0)
                self.total_kills = data.get("total_kills", 0)
                self.total_playtime = data.get("total_playtime", 0)
                self.unlocked_ships = data.get("unlocked_ships", ["default"])
                self.upgrades = data.get("upgrades", {"damage": 0, "speed": 0, "fire_rate": 0, "health": 0, "shield": 0})
                self.coins = data.get("coins", 0)
        except:
            self.save()
            
    def save(self):
        data = {
            "high_score": self.high_score,
            "total_kills": self.total_kills,
            "total_playtime": self.total_playtime,
            "unlocked_ships": self.unlocked_ships,
            "upgrades": self.upgrades,
            "coins": self.coins
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

save_data = SaveData()
save_data.load()

# ================= TEXT HELPER FUNCTION =================
def draw_text(surface, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

# ================= VISUAL EFFECTS =================
class Particle:
    def __init__(self, pos, color=None, size=2, velocity=None, lifetime=30, trail=False):
        self.pos = list(pos)
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.trail = trail
        self.color = color or random.choice(PARTICLE_COLORS)
        self.velocity = velocity or [random.uniform(-3, 3), random.uniform(-3, 3)]
        self.gravity = 0.1 if not trail else 0
        
    def update(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.velocity[1] += self.gravity
        self.lifetime -= 1
        
        # Air resistance
        self.velocity[0] *= 0.98
        self.velocity[1] *= 0.98
        
        return self.lifetime > 0
        
    def draw(self, surface):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        if self.trail:
            # Draw trail line
            end_pos = (self.pos[0] - self.velocity[0]*2, 
                      self.pos[1] - self.velocity[1]*2)
            
            # Create surface for line with alpha
            line_surf = pygame.Surface((abs(self.pos[0]-end_pos[0])+self.size*2, 
                                       abs(self.pos[1]-end_pos[1])+self.size*2), 
                                      pygame.SRCALPHA)
            color_with_alpha = (*self.color, alpha)
            pygame.draw.line(line_surf, color_with_alpha, 
                           (self.size, self.size), 
                           (end_pos[0]-self.pos[0]+self.size, 
                            end_pos[1]-self.pos[1]+self.size), 
                           self.size)
            surface.blit(line_surf, (self.pos[0]-self.size, self.pos[1]-self.size))
        else:
            # Draw particle circle with glow
            glow_surf = pygame.Surface((self.size*4, self.size*4), pygame.SRCALPHA)
            radius = self.size * (self.lifetime / self.max_lifetime)
            pygame.draw.circle(glow_surf, (*self.color, alpha//2), 
                             (self.size*2, self.size*2), radius*2)
            pygame.draw.circle(glow_surf, (*self.color, alpha), 
                             (self.size*2, self.size*2), radius)
            surface.blit(glow_surf, (self.pos[0]-self.size*2, self.pos[1]-self.size*2))

particles = []
effects = []

class VisualEffect:
    def __init__(self, pos, effect_type, duration=30):
        self.pos = pos
        self.type = effect_type
        self.duration = duration
        self.time = 0
        self.size = 0
        
    def update(self):
        self.time += 1
        if self.time > self.duration:
            return False
        
        if self.type == "explosion":
            self.size = 30 * (1 - (self.time / self.duration))
        elif self.type == "powerup":
            self.size = 20 + 10 * math.sin(self.time * 0.3)
        elif self.type == "hit":
            self.size = 15 * (1 - (self.time / self.duration))
            
        return True
        
    def draw(self, surface):
        if self.type == "explosion":
            # Shockwave rings
            for i in range(3):
                radius = self.size + i * 10
                alpha = 150 - i * 50 - (self.time * 2)
                if alpha > 0:
                    color = (*CYBER_YELLOW, alpha)
                    pygame.draw.circle(surface, color, 
                                     (int(self.pos[0]), int(self.pos[1])), 
                                     int(radius), 2)
                    
        elif self.type == "powerup":
            # Rotating hexagon
            angle = self.time * 0.2
            points = []
            for i in range(6):
                rad = angle + i * math.pi / 3
                x = self.pos[0] + math.cos(rad) * self.size
                y = self.pos[1] + math.sin(rad) * self.size
                points.append((x, y))
            
            # Draw with gradient
            for i in range(len(points)):
                pygame.draw.line(surface, CYBER_GREEN, 
                               points[i], points[(i+1)%len(points)], 3)
                
        elif self.type == "hit":
            # X mark
            size = self.size
            pygame.draw.line(surface, (*CYBER_RED, 200), 
                           (self.pos[0]-size, self.pos[1]-size),
                           (self.pos[0]+size, self.pos[1]+size), 4)
            pygame.draw.line(surface, (*CYBER_RED, 200),
                           (self.pos[0]+size, self.pos[1]-size),
                           (self.pos[0]-size, self.pos[1]+size), 4)

def add_effect(pos, effect_type, duration=30):
    effects.append(VisualEffect(pos, effect_type, duration))

# ================= BACKGROUND =================
class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.5, 2.0)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(150, 255)
        self.pulse = random.random() * math.pi * 2
        
    def update(self, speed_factor=1.0):
        self.x -= self.speed * speed_factor
        if self.x < 0:
            self.x = WIDTH
            self.y = random.randint(0, HEIGHT)
            
        self.pulse += 0.05
        self.brightness = 150 + int(100 * math.sin(self.pulse))
        
    def draw(self, surface):
        color = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)

class Nebula:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(100, 300)
        self.color = random.choice(PARTICLE_COLORS)
        self.alpha = random.randint(20, 60)
        self.speed = random.uniform(0.1, 0.5)
        
    def update(self, speed_factor=1.0):
        self.x -= self.speed * speed_factor
        if self.x < -self.size:
            self.x = WIDTH + self.size
            self.y = random.randint(0, HEIGHT)
            
    def draw(self, surface):
        nebula_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        for i in range(3):
            radius = self.size - i * 30
            alpha = self.alpha - i * 10
            if alpha > 0 and radius > 0:
                pygame.draw.circle(nebula_surf, (*self.color, alpha), 
                                 (self.size, self.size), radius)
        surface.blit(nebula_surf, (int(self.x - self.size), int(self.y - self.size)))

stars = [Star() for _ in range(100)]
nebulas = [Nebula() for _ in range(3)]

def draw_background(surface, speed_factor=1.0):
    # Deep space gradient
    for y in range(HEIGHT):
        color_value = 10 + y // 40
        color = (color_value, color_value + 5, color_value + 10)
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))
    
    # Update and draw nebulas
    for nebula in nebulas:
        nebula.update(speed_factor * 0.5)
        nebula.draw(surface)
    
    # Update and draw stars with parallax
    for star in stars:
        star.update(speed_factor)
        star.draw(surface)
    
    # Grid lines in background
    for x in range(0, WIDTH, 50):
        pygame.draw.line(surface, (100, 100, 200, 30), 
                        (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(surface, (100, 100, 200, 30), 
                        (0, y), (WIDTH, y), 1)
    
    # Scan line effect
    scan_y = (pygame.time.get_ticks() // 20) % HEIGHT
    pygame.draw.line(surface, (0, 255, 255, 50), (0, scan_y), (WIDTH, scan_y), 2)

# ================= PLAYER =================
class Player:
    def __init__(self):
        self.rect = pygame.Rect(80, HEIGHT//2, 42, 42)
        self.speed = BASE_SPEED + save_data.upgrades["speed"] * 0.5
        self.health = 3 + save_data.upgrades["health"]
        self.max_health = 3 + save_data.upgrades["health"]
        self.inv = 0
        self.bullets = []
        self.fire = 0
        self.fire_rate = PLAYER_FIRE_RATE - save_data.upgrades["fire_rate"] * 2
        self.trail = []
        self.angle = 0
        self.damage = 1 + save_data.upgrades["damage"] * 0.5
        self.shield = False
        self.shield_time = 0
        self.ship_type = "default"
        self.coins = save_data.coins
        
    def update(self, keys):
        # Movement with smoother acceleration
        move_y = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y += self.speed
            
        # Convert to integer for rect position
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y + int(move_y)))
        
        # Calculate rotation based on movement
        if move_y != 0:
            self.angle = move_y * 0.1
        else:
            self.angle *= 0.9
        
        # Shooting
        self.fire += 1
        if self.fire > self.fire_rate and (keys[pygame.K_SPACE] or keys[pygame.K_z]):
            self.shoot()
            self.fire = 0
            
        # Update trail
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 20:
            self.trail.pop(0)
            
        # Add trail particles
        if len(self.trail) > 1:
            particles.append(Particle(
                self.rect.center,
                CYBER_BLUE,
                size=2,
                velocity=[random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)],
                lifetime=20,
                trail=False
            ))
            
        # Update shield
        if self.shield_time > 0:
            self.shield_time -= 1
            self.shield = True
        else:
            self.shield = False
            
        # Update invincibility
        if self.inv > 0:
            self.inv -= 1
            
    def shoot(self):
        bullet_x = self.rect.right
        bullet_y = self.rect.centery - 2
        
        # Different bullet patterns based on upgrades
        bullet_count = 1 + min(2, save_data.upgrades["damage"] // 2)
        
        for i in range(bullet_count):
            offset = (i - (bullet_count - 1) / 2) * 8
            self.bullets.append({
                "rect": pygame.Rect(bullet_x, bullet_y + offset, 16, 6),
                "damage": self.damage,
                "type": "player",
                "color": CYBER_BLUE
            })
            
        # Muzzle flash
        for _ in range(10):
            particles.append(Particle(
                (self.rect.right, self.rect.centery),
                CYBER_YELLOW,
                size=random.randint(2, 4),
                velocity=[random.uniform(3, 6), random.uniform(-2, 2)],
                lifetime=15
            ))
        
    def draw(self, surface):
        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = 100 - i * 5
            if alpha > 0:
                trail_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (*CYBER_BLUE, alpha), 
                                 (5, 5), 5 - i//4)
                surface.blit(trail_surf, (pos[0]-5, pos[1]-5))
        
        # Draw player ship with rotation
        ship_surf = pygame.Surface((self.rect.width + 10, self.rect.height + 10), 
                                 pygame.SRCALPHA)
        
        # Ship body
        points = [
            (10, self.rect.height//2),  # Left point
            (self.rect.width + 5, 5),   # Top right
            (self.rect.width + 5, self.rect.height - 5)  # Bottom right
        ]
        
        # Draw with gradient
        for i in range(3):
            color = (CYBER_BLUE[0], CYBER_BLUE[1], CYBER_BLUE[2], 200 - i*50)
            scaled_points = [(x+i*2, y) for x, y in points]
            pygame.draw.polygon(ship_surf, color, scaled_points)
        
        # Rotate ship
        rotated_ship = pygame.transform.rotate(ship_surf, self.angle * 10)
        ship_rect = rotated_ship.get_rect(center=self.rect.center)
        surface.blit(rotated_ship, ship_rect)
        
        # Shield
        if self.shield:
            shield_alpha = 100 + int(100 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.circle(surface, (*CYBER_GREEN, shield_alpha), 
                             self.rect.center, 25, 3)
            
        # Health display on player
        for i in range(self.max_health):
            color = CYBER_GREEN if i < self.health else (50, 50, 50)
            pygame.draw.rect(surface, color, 
                           (self.rect.x + i * 10, self.rect.y - 15, 8, 4))
            
        # Invincibility flash
        if self.inv > 0 and self.inv % 4 < 2:
            flash_surf = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(flash_surf, (*NEON_WHITE, 100), 
                           (0, 0, self.rect.width + 10, self.rect.height + 10), 2, 5)
            surface.blit(flash_surf, (self.rect.x-5, self.rect.y-5))

player = Player()

# ================= ENEMIES =================
class Enemy:
    def __init__(self, boss=False, level=1):
        self.boss = boss
        self.level = level
        self.bullets = []  # FIXED: Initialize bullets for ALL enemies
        
        if boss:
            self.size = 80 + level * 5
            self.rect = pygame.Rect(WIDTH + 40, random.randint(0, HEIGHT - self.size), 
                                  self.size, self.size)
            self.hp = 20 + level * 5
            self.max_hp = 20 + level * 5
            self.speed = 2
            self.color = CYBER_PURPLE
            self.attack_pattern = 0
            self.attack_timer = 0
        else:
            enemy_types = ["normal", "fast", "tank", "shooter", "zigzag"]
            weights = [0.3, 0.2, 0.2, 0.15, 0.15]
            self.type = random.choices(enemy_types, weights=weights)[0]
            
            if self.type == "normal":
                self.size = 35
                self.hp = 2
                self.speed = 4
                self.color = CYBER_RED
            elif self.type == "fast":
                self.size = 25
                self.hp = 1
                self.speed = 7
                self.color = CYBER_PINK
            elif self.type == "tank":
                self.size = 50
                self.hp = 5
                self.speed = 2.5
                self.color = (255, 100, 0)
            elif self.type == "shooter":
                self.size = 40
                self.hp = 3
                self.speed = 3
                self.color = CYBER_GREEN
                self.shoot_timer = 0
            elif self.type == "zigzag":
                self.size = 30
                self.hp = 2
                self.speed = 4
                self.color = CYBER_YELLOW
                self.zig_dir = random.choice([-1, 1])
                self.zig_timer = 0
                
            self.rect = pygame.Rect(WIDTH + 40, random.randint(0, HEIGHT - self.size), 
                                  self.size, self.size)
            self.max_hp = self.hp
            
    def update(self, player_pos):
        if self.boss:
            self.update_boss(player_pos)
        else:
            self.rect.x -= int(self.speed)
            
            if self.type == "zigzag":
                self.zig_timer += 1
                if self.zig_timer > 20:
                    self.zig_dir *= -1
                    self.zig_timer = 0
                self.rect.y += self.zig_dir * 2
                self.rect.y = max(0, min(HEIGHT - self.size, self.rect.y))
                
            elif self.type == "shooter":
                self.shoot_timer += 1
                if self.shoot_timer > 60:
                    dx = player_pos[0] - self.rect.centerx
                    dy = player_pos[1] - self.rect.centery
                    dist = max(1, math.sqrt(dx*dx + dy*dy))
                    self.bullets.append({
                        "rect": pygame.Rect(self.rect.left - 10, self.rect.centery - 3, 12, 6),
                        "vel": [-dx/dist * 5, -dy/dist * 5],
                        "color": CYBER_GREEN
                    })
                    self.shoot_timer = 0
        
        # Update enemy bullets for ALL enemies
        for bullet in self.bullets[:]:
            bullet["rect"].x += bullet["vel"][0]
            bullet["rect"].y += bullet["vel"][1]
            
            if bullet["rect"].right < 0 or bullet["rect"].left > WIDTH:
                self.bullets.remove(bullet)
                
    def update_boss(self, player_pos):
        self.attack_timer += 1
        
        # Movement pattern
        self.rect.y += int(math.sin(self.attack_timer * 0.03) * 2)
        self.rect.x -= int(self.speed)
        
        # Attack patterns
        if self.attack_pattern == 0:
            if self.attack_timer % 30 == 0:
                # Spread shot
                for angle in range(-30, 31, 15):
                    rad = math.radians(angle)
                    self.bullets.append({
                        "rect": pygame.Rect(self.rect.left - 10, self.rect.centery - 4, 16, 8),
                        "vel": [-math.cos(rad) * 4, -math.sin(rad) * 4],
                        "color": CYBER_PURPLE
                    })
                    
            if self.hp < self.max_hp // 2:
                self.attack_pattern = 1
                self.attack_timer = 0
                
        elif self.attack_pattern == 1:
            if self.attack_timer % 20 == 0:
                # Targeted shots
                dx = player_pos[0] - self.rect.centerx
                dy = player_pos[1] - self.rect.centery
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                self.bullets.append({
                    "rect": pygame.Rect(self.rect.left - 10, self.rect.centery - 4, 16, 8),
                    "vel": [-dx/dist * 6, -dy/dist * 6],
                    "color": CYBER_PINK
                })
                
    def draw(self, surface):
        if self.boss:
            # Boss with special effects
            boss_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            
            # Boss core
            pygame.draw.circle(boss_surf, self.color, 
                             (self.size//2, self.size//2), self.size//3)
            
            # Rotating rings
            ring_time = pygame.time.get_ticks() * 0.001
            for i in range(3):
                radius = self.size//2 - i * 5
                points = []
                for j in range(8):
                    angle = ring_time + j * math.pi / 4
                    x = self.size//2 + math.cos(angle) * radius
                    y = self.size//2 + math.sin(angle) * radius
                    points.append((x, y))
                
                for j in range(len(points)):
                    pygame.draw.line(boss_surf, CYBER_PINK, 
                                   points[j], points[(j+1)%len(points)], 2)
                    
            surface.blit(boss_surf, self.rect)
            
            # Health bar
            bar_width = 120
            bar_height = 10
            bar_x = self.rect.centerx - bar_width//2
            bar_y = self.rect.y - 25
            
            # Background
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), 0, 5)
            
            # Health
            health_width = (self.hp / self.max_hp) * bar_width
            health_color = CYBER_GREEN if self.hp > self.max_hp//2 else CYBER_YELLOW
            pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height), 0, 5)
            
            # Border
            pygame.draw.rect(surface, NEON_WHITE, (bar_x, bar_y, bar_width, bar_height), 2, 5)
            
            # Boss name
            name_text = FONT.render("SYSTEM OVERLORD", True, CYBER_PURPLE)
            surface.blit(name_text, (self.rect.centerx - name_text.get_width()//2, bar_y - 30))
            
        else:
            # Regular enemy
            enemy_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            
            # Different shapes for different types
            if self.type == "normal":
                pygame.draw.rect(enemy_surf, self.color, (0, 0, self.size, self.size), 0, 8)
            elif self.type == "fast":
                points = [(self.size//2, 0), (self.size, self.size), (0, self.size)]
                pygame.draw.polygon(enemy_surf, self.color, points)
            elif self.type == "tank":
                pygame.draw.circle(enemy_surf, self.color, (self.size//2, self.size//2), self.size//2)
            elif self.type == "shooter":
                pygame.draw.rect(enemy_surf, self.color, (0, self.size//3, self.size, self.size//3), 0, 5)
            elif self.type == "zigzag":
                pygame.draw.polygon(enemy_surf, self.color, 
                                  [(0, 0), (self.size, self.size//2), (0, self.size)])
                
            # Health indicator
            health_ratio = self.hp / self.max_hp
            if health_ratio < 1:
                pygame.draw.rect(enemy_surf, CYBER_RED, 
                               (0, 0, self.size * health_ratio, 3))
                
            surface.blit(enemy_surf, self.rect)
            
        # Draw enemy bullets
        for bullet in self.bullets:
            pygame.draw.rect(surface, bullet["color"], bullet["rect"], 0, 3)

enemies = []
enemy_timer = 0

# ================= POWER-UPS =================
class PowerUp:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], 32, 32)
        self.type = random.choice(["health", "shield", "speed", "weapon", "coin"])
        self.float_offset = random.random() * math.pi * 2
        self.collected = False
        
        if self.type == "health":
            self.color = CYBER_GREEN
            self.symbol = "+"
        elif self.type == "shield":
            self.color = CYBER_BLUE
            self.symbol = "S"
        elif self.type == "speed":
            self.color = CYBER_PINK
            self.symbol = "F"
        elif self.type == "weapon":
            self.color = CYBER_YELLOW
            self.symbol = "W"
        else:  # coin
            self.color = CYBER_YELLOW
            self.symbol = "$"
            
    def update(self):
        self.float_offset += 0.05
        self.rect.y = int(self.rect.y + math.sin(self.float_offset) * 0.5)
        
    def draw(self, surface):
        if self.collected:
            return
            
        # Glow effect
        glow_size = 40
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_alpha = 100 + int(100 * math.sin(pygame.time.get_ticks() * 0.005))
        pygame.draw.circle(glow_surf, (*self.color, glow_alpha), 
                         (glow_size//2, glow_size//2), glow_size//2)
        surface.blit(glow_surf, (self.rect.centerx - glow_size//2, 
                               self.rect.centery - glow_size//2))
        
        # Main body
        powerup_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.circle(powerup_surf, self.color, 
                         (self.rect.width//2, self.rect.height//2), 
                         self.rect.width//2 - 4)
        pygame.draw.circle(powerup_surf, NEON_WHITE, 
                         (self.rect.width//2, self.rect.height//2), 
                         self.rect.width//2 - 4, 2)
        
        # Symbol
        symbol = FONT.render(self.symbol, True, NEON_WHITE)
        powerup_surf.blit(symbol, 
                         (self.rect.width//2 - symbol.get_width()//2,
                          self.rect.height//2 - symbol.get_height()//2))
        
        surface.blit(powerup_surf, self.rect)

powerups = []

# ================= UI =================
class Button:
    def __init__(self, x, y, w, h, text, color=CYBER_BLUE, hover_color=CYBER_PINK):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, 0, 10)
        pygame.draw.rect(surface, NEON_WHITE, self.rect, 2, 10)
        
        text_surf = FONT.render(self.text, True, NEON_WHITE)
        surface.blit(text_surf, 
                    (self.rect.centerx - text_surf.get_width()//2,
                     self.rect.centery - text_surf.get_height()//2))
        
    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click

# ================= GAME STATES =================
class GameState:
    MENU = 0
    PLAYING = 1
    UPGRADES = 2
    GAME_OVER = 3

current_state = GameState.MENU
score = 0
level = 1
combo = 1
combo_timer = 0
game_time = 0
screen_shake = 0
shake_intensity = 0

# UI Buttons
play_button = Button(WIDTH//2 - 100, HEIGHT//2, 200, 50, "START MISSION")
shop_button = Button(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50, "UPGRADE HANGAR")
quit_button = Button(WIDTH//2 - 100, HEIGHT//2 + 140, 200, 50, "EXIT TERMINAL")
resume_button = Button(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50, "RESTART")
menu_button = Button(WIDTH//2 - 100, HEIGHT//2 + 140, 200, 50, "MAIN MENU")

# Upgrade buttons
upgrade_buttons = [
    Button(150, 150, 200, 50, "DAMAGE: " + str(save_data.upgrades["damage"])),
    Button(150, 220, 200, 50, "SPEED: " + str(save_data.upgrades["speed"])),
    Button(150, 290, 200, 50, "FIRE RATE: " + str(save_data.upgrades["fire_rate"])),
    Button(150, 360, 200, 50, "HEALTH: " + str(save_data.upgrades["health"])),
    Button(150, 430, 200, 50, "SHIELD: " + str(save_data.upgrades["shield"])),
    Button(550, 150, 200, 50, "BACK")
]

# ================= MAIN GAME LOOP =================
running = True
while running:
    delta_time = CLOCK.tick(FPS) / 1000.0
    game_time += delta_time
    
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = False
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_click = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if current_state == GameState.PLAYING:
                    current_state = GameState.MENU
                elif current_state == GameState.UPGRADES:
                    current_state = GameState.MENU
            elif event.key == pygame.K_r and current_state == GameState.GAME_OVER:
                # Reset game
                current_state = GameState.PLAYING
                score = 0
                level = 1
                player.health = player.max_health
                enemies.clear()
                player.bullets.clear()
                particles.clear()
                effects.clear()
                powerups.clear()
                # Reset player position
                player.rect.x = 80
                player.rect.y = HEIGHT//2
    
    # Clear screen
    SCREEN.fill(DARK_BG)
    
    # Draw background with speed based on game state
    bg_speed = 1.0
    if current_state == GameState.PLAYING:
        bg_speed = 1.5 + level * 0.1
    draw_background(SCREEN, bg_speed)
    
    # Apply screen shake
    shake_offset = (0, 0)
    if screen_shake > 0:
        screen_shake -= 1
        shake_offset = (random.uniform(-shake_intensity, shake_intensity),
                       random.uniform(-shake_intensity, shake_intensity))
    
    # Create a surface for game elements
    game_surface = SCREEN if screen_shake == 0 else pygame.Surface((WIDTH, HEIGHT))
    if screen_shake > 0:
        game_surface.fill(DARK_BG)
    
    # Update based on game state
    if current_state == GameState.MENU:
        # Update buttons
        play_button.update(mouse_pos)
        shop_button.update(mouse_pos)
        quit_button.update(mouse_pos)
        
        # Check clicks
        if play_button.is_clicked(mouse_pos, mouse_click):
            current_state = GameState.PLAYING
            # Reset game state when starting
            score = 0
            level = 1
            player.health = player.max_health
            enemies.clear()
            player.bullets.clear()
            particles.clear()
            effects.clear()
            powerups.clear()
            player.rect.x = 80
            player.rect.y = HEIGHT//2
        elif shop_button.is_clicked(mouse_pos, mouse_click):
            current_state = GameState.UPGRADES
        elif quit_button.is_clicked(mouse_pos, mouse_click):
            running = False
            
        # Draw menu
        title_text = FONT_TITLE.render("NEO DODGE", True, CYBER_BLUE)
        game_surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 80))
        
        subtitle = FONT.render("CYBER ARENA", True, CYBER_PINK)
        game_surface.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 160))
        
        high_score_text = FONT.render(f"HIGH SCORE: {save_data.high_score}", True, CYBER_YELLOW)
        game_surface.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, 220))
        
        play_button.draw(game_surface)
        shop_button.draw(game_surface)
        quit_button.draw(game_surface)
        
        # Draw animated ships in background
        for i in range(3):
            x = 100 + i * 250
            y = 400 + math.sin(game_time + i) * 20
            pygame.draw.polygon(game_surface, CYBER_BLUE, 
                              [(x, y), (x+40, y-20), (x+40, y+20)])
            
    elif current_state == GameState.PLAYING:
        keys = pygame.key.get_pressed()
        
        # Update player
        player.update(keys)
        
        # Spawn enemies
        enemy_timer += 1
        if enemy_timer > max(20, 60 - level * 2):
            if level % BOSS_LEVEL_INTERVAL == 0 and not any(e.boss for e in enemies):
                enemies.append(Enemy(boss=True, level=level))
            else:
                enemies.append(Enemy(level=level))
            enemy_timer = 0
            
        # Spawn power-ups randomly
        if random.random() < 0.01:
            powerups.append(PowerUp((random.randint(WIDTH//2, WIDTH-50), 
                                   random.randint(50, HEIGHT-50))))
        
        # Update player bullets
        for bullet in player.bullets[:]:
            bullet["rect"].x += 12
            if bullet["rect"].left > WIDTH:
                player.bullets.remove(bullet)
            
        # Update enemies
        for enemy in enemies[:]:
            enemy.update(player.rect.center)
            
            # Check if enemy is off screen
            if enemy.rect.right < -50:
                enemies.remove(enemy)
                combo = 1
                continue
                
            # Check collision with player bullets
            for bullet in player.bullets[:]:
                if bullet["rect"].colliderect(enemy.rect):
                    enemy.hp -= bullet["damage"]
                    player.bullets.remove(bullet)
                    
                    # Hit effect
                    add_effect(bullet["rect"].center, "hit", 15)
                    for _ in range(10):
                        particles.append(Particle(
                            bullet["rect"].center,
                            enemy.color,
                            size=random.randint(2, 4),
                            velocity=[random.uniform(-3, 3), random.uniform(-3, 3)],
                            lifetime=20
                        ))
                    
                    if enemy.hp <= 0:
                        # Enemy destroyed
                        enemies.remove(enemy)
                        
                        # Score calculation
                        base_score = 100 if enemy.boss else 10
                        score += base_score * combo
                        player.coins += 1 if not enemy.boss else 5
                        
                        # Combo system
                        combo = min(combo + 1, 10)
                        combo_timer = 180  # 3 seconds to maintain combo
                        
                        # Explosion effect
                        add_effect(enemy.rect.center, "explosion", 40)
                        for _ in range(30):
                            particles.append(Particle(
                                enemy.rect.center,
                                enemy.color,
                                size=random.randint(3, 6),
                                velocity=[random.uniform(-8, 8), random.uniform(-8, 8)],
                                lifetime=random.randint(20, 40)
                            ))
                        
                        # Screen shake
                        screen_shake = 20 if enemy.boss else 10
                        shake_intensity = 5 if enemy.boss else 3
                        
                        # Chance to drop power-up
                        if random.random() < 0.3:
                            powerups.append(PowerUp((enemy.rect.centerx, enemy.rect.centery)))
                            
                        # Check for level up
                        if score // 1000 + 1 > level:
                            level += 1
                            add_effect((WIDTH//2, HEIGHT//2), "powerup", 60)
                            
                        break
                        
            # Check collision with player
            if enemy.rect.colliderect(player.rect) and player.inv == 0:
                if player.shield:
                    player.shield_time = 0
                    add_effect(player.rect.center, "hit", 20)
                else:
                    player.health -= 1
                    player.inv = 60
                    screen_shake = 15
                    shake_intensity = 4
                    
                    # Damage effect
                    add_effect(player.rect.center, "hit", 20)
                    for _ in range(20):
                        particles.append(Particle(
                            player.rect.center,
                            CYBER_RED,
                            size=random.randint(2, 5),
                            velocity=[random.uniform(-5, 5), random.uniform(-5, 5)],
                            lifetime=25
                        ))
                    
                    if player.health <= 0:
                        # Game over
                        current_state = GameState.GAME_OVER
                        save_data.high_score = max(save_data.high_score, score)
                        save_data.total_kills += score // 10
                        save_data.coins = player.coins
                        save_data.save()
                        
                # Remove non-boss enemies on collision
                if not enemy.boss:
                    enemies.remove(enemy)
                    
            # Check enemy bullets collision with player
            for bullet in enemy.bullets[:]:
                if bullet["rect"].colliderect(player.rect) and player.inv == 0:
                    if player.shield:
                        player.shield_time = max(0, player.shield_time - 60)
                        enemy.bullets.remove(bullet)
                    else:
                        player.health -= 1
                        player.inv = 60
                        enemy.bullets.remove(bullet)
                        
                        if player.health <= 0:
                            current_state = GameState.GAME_OVER
                            save_data.high_score = max(save_data.high_score, score)
                            save_data.total_kills += score // 10
                            save_data.coins = player.coins
                            save_data.save()
                            
        # Update power-ups
        for powerup in powerups[:]:
            powerup.update()
            
            if powerup.rect.colliderect(player.rect) and not powerup.collected:
                powerup.collected = True
                add_effect(powerup.rect.center, "powerup", 30)
                
                # Apply power-up effect
                if powerup.type == "health":
                    player.health = min(player.max_health, player.health + 1)
                elif powerup.type == "shield":
                    player.shield_time = 300
                elif powerup.type == "speed":
                    player.speed += 2
                elif powerup.type == "weapon":
                    player.damage += 0.5
                elif powerup.type == "coin":
                    player.coins += random.randint(1, 5)
                    
                powerups.remove(powerup)
                
        # Update combo timer
        if combo_timer > 0:
            combo_timer -= 1
            if combo_timer == 0:
                combo = 1
                
        # Update particles
        particles = [p for p in particles if p.update()]
        
        # Update effects
        effects = [e for e in effects if e.update()]
        
        # Draw everything
        for p in particles:
            p.draw(game_surface)
            
        for e in effects:
            e.draw(game_surface)
            
        for bullet in player.bullets:
            pygame.draw.rect(game_surface, bullet["color"], bullet["rect"], 0, 3)
            
        for enemy in enemies:
            enemy.draw(game_surface)
            
        for powerup in powerups:
            powerup.draw(game_surface)
            
        player.draw(game_surface)
        
        # Draw UI
        # Top bar
        top_bar = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
        top_bar.fill((*UI_BLUE, 200))
        game_surface.blit(top_bar, (0, 0))
        pygame.draw.line(game_surface, CYBER_BLUE, (0, 60), (WIDTH, 60), 3)
        
        # Score
        draw_text(game_surface, f"SCORE: {score:06d}", FONT, NEON_WHITE, 20, 15)
        draw_text(game_surface, f"HIGH: {save_data.high_score:06d}", FONT, CYBER_YELLOW, 200, 15)
        draw_text(game_surface, f"LEVEL: {level:02d}", FONT, CYBER_GREEN, 380, 15)
        
        # Combo
        if combo > 1:
            combo_text = FONT_LARGE.render(f"x{combo} COMBO!", True, CYBER_PINK)
            combo_alpha = min(255, combo_timer * 2)
            combo_text.set_alpha(combo_alpha)
            game_surface.blit(combo_text, (WIDTH//2 - combo_text.get_width()//2, 80))
            
        # Coins
        coin_text = FONT.render(f"COINS: {player.coins}", True, CYBER_YELLOW)
        game_surface.blit(coin_text, (WIDTH - 150, 15))
        
        # Health bar
        health_width = 200
        health_height = 20
        health_x = WIDTH - health_width - 20
        health_y = 45
        
        # Background
        pygame.draw.rect(game_surface, (50, 50, 50), 
                        (health_x, health_y, health_width, health_height), 0, 10)
        
        # Health fill
        health_ratio = player.health / player.max_health
        health_fill_width = health_width * health_ratio
        health_color = CYBER_GREEN if health_ratio > 0.5 else CYBER_YELLOW if health_ratio > 0.2 else CYBER_RED
        pygame.draw.rect(game_surface, health_color, 
                        (health_x, health_y, health_fill_width, health_height), 0, 10)
        
        # Border
        pygame.draw.rect(game_surface, NEON_WHITE, 
                        (health_x, health_y, health_width, health_height), 2, 10)
        
        # Health text
        health_text = FONT_SMALL.render(f"SHIELD: {player.health}/{player.max_health}", True, NEON_WHITE)
        game_surface.blit(health_text, (health_x + 10, health_y + 2))
        
        # Controls hint
        controls = FONT_SMALL.render("ARROWS/WASD: MOVE | SPACE/Z: FIRE | ESC: MENU", True, CYBER_BLUE)
        game_surface.blit(controls, (WIDTH//2 - controls.get_width()//2, HEIGHT - 30))
        
    elif current_state == GameState.UPGRADES:
        # Update upgrade buttons
        upgrade_buttons[0].text = f"DAMAGE: {save_data.upgrades['damage']}/5 - {50 * (save_data.upgrades['damage'] + 1)} COINS"
        upgrade_buttons[1].text = f"SPEED: {save_data.upgrades['speed']}/5 - {40 * (save_data.upgrades['speed'] + 1)} COINS"
        upgrade_buttons[2].text = f"FIRE RATE: {save_data.upgrades['fire_rate']}/5 - {60 * (save_data.upgrades['fire_rate'] + 1)} COINS"
        upgrade_buttons[3].text = f"HEALTH: {save_data.upgrades['health']}/5 - {80 * (save_data.upgrades['health'] + 1)} COINS"
        upgrade_buttons[4].text = f"SHIELD: {save_data.upgrades['shield']}/5 - {70 * (save_data.upgrades['shield'] + 1)} COINS"
        
        for button in upgrade_buttons:
            button.update(mouse_pos)
            
        # Check for upgrades
        if mouse_click:
            for i, button in enumerate(upgrade_buttons):
                if button.is_clicked(mouse_pos, True):
                    if i == 0 and player.coins >= 50 * (save_data.upgrades["damage"] + 1) and save_data.upgrades["damage"] < 5:
                        player.coins -= 50 * (save_data.upgrades["damage"] + 1)
                        save_data.upgrades["damage"] += 1
                        player.damage = 1 + save_data.upgrades["damage"] * 0.5
                        save_data.save()
                    elif i == 1 and player.coins >= 40 * (save_data.upgrades["speed"] + 1) and save_data.upgrades["speed"] < 5:
                        player.coins -= 40 * (save_data.upgrades["speed"] + 1)
                        save_data.upgrades["speed"] += 1
                        player.speed = BASE_SPEED + save_data.upgrades["speed"] * 0.5
                        save_data.save()
                    elif i == 2 and player.coins >= 60 * (save_data.upgrades["fire_rate"] + 1) and save_data.upgrades["fire_rate"] < 5:
                        player.coins -= 60 * (save_data.upgrades["fire_rate"] + 1)
                        save_data.upgrades["fire_rate"] += 1
                        player.fire_rate = PLAYER_FIRE_RATE - save_data.upgrades["fire_rate"] * 2
                        save_data.save()
                    elif i == 3 and player.coins >= 80 * (save_data.upgrades["health"] + 1) and save_data.upgrades["health"] < 5:
                        player.coins -= 80 * (save_data.upgrades["health"] + 1)
                        save_data.upgrades["health"] += 1
                        player.max_health = 3 + save_data.upgrades["health"]
                        player.health = player.max_health
                        save_data.save()
                    elif i == 4 and player.coins >= 70 * (save_data.upgrades["shield"] + 1) and save_data.upgrades["shield"] < 5:
                        player.coins -= 70 * (save_data.upgrades["shield"] + 1)
                        save_data.upgrades["shield"] += 1
                        save_data.save()
                    elif i == 5:
                        current_state = GameState.MENU
                        
        # Draw shop
        title = FONT_TITLE.render("UPGRADE HANGAR", True, CYBER_BLUE)
        game_surface.blit(title, (WIDTH//2 - title.get_width()//2, 40))
        
        coins_text = FONT_LARGE.render(f"COINS: {player.coins}", True, CYBER_YELLOW)
        game_surface.blit(coins_text, (WIDTH//2 - coins_text.get_width()//2, 100))
        
        for button in upgrade_buttons:
            button.draw(game_surface)
            
        # Draw player preview
        preview_rect = pygame.Rect(550, 250, 100, 100)
        pygame.draw.rect(game_surface, CYBER_BLUE, preview_rect, 0, 10)
        pygame.draw.rect(game_surface, NEON_WHITE, preview_rect, 2, 10)
        
        ship_preview = FONT.render("SHIP", True, NEON_WHITE)
        game_surface.blit(ship_preview, (preview_rect.centerx - ship_preview.get_width()//2,
                                       preview_rect.centery - ship_preview.get_height()//2))
        
        stats_y = 370
        stats = [
            f"DAMAGE: {player.damage:.1f}",
            f"SPEED: {player.speed:.1f}",
            f"FIRE RATE: {60/(player.fire_rate/60):.1f}/sec",
            f"HEALTH: {player.health}/{player.max_health}",
            f"SHIELD TIME: {save_data.upgrades['shield'] * 2}s"
        ]
        
        for i, stat in enumerate(stats):
            draw_text(game_surface, stat, FONT_SMALL, NEON_WHITE, 550, stats_y + i * 25)
            
    elif current_state == GameState.GAME_OVER:
        # Update buttons
        resume_button.text = f"RESTART (SCORE: {score})"
        resume_button.update(mouse_pos)
        menu_button.update(mouse_pos)
        
        if resume_button.is_clicked(mouse_pos, mouse_click):
            current_state = GameState.PLAYING
            score = 0
            level = 1
            player.health = player.max_health
            enemies.clear()
            player.bullets.clear()
            particles.clear()
            effects.clear()
            powerups.clear()
            # Reset player position
            player.rect.x = 80
            player.rect.y = HEIGHT//2
        elif menu_button.is_clicked(mouse_pos, mouse_click):
            current_state = GameState.MENU
            
        # Draw game over screen
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        game_surface.blit(overlay, (0, 0))
        
        game_over_text = FONT_TITLE.render("MISSION FAILED", True, CYBER_RED)
        game_surface.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 80))
        
        score_text = FONT_LARGE.render(f"FINAL SCORE: {score}", True, CYBER_YELLOW)
        game_surface.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 180))
        
        high_text = FONT.render(f"HIGH SCORE: {save_data.high_score}", True, CYBER_GREEN)
        game_surface.blit(high_text, (WIDTH//2 - high_text.get_width()//2, 240))
        
        level_text = FONT.render(f"LEVEL REACHED: {level}", True, CYBER_BLUE)
        game_surface.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 280))
        
        coins_text = FONT.render(f"COINS EARNED: {player.coins}", True, CYBER_PINK)
        game_surface.blit(coins_text, (WIDTH//2 - coins_text.get_width()//2, 320))
        
        resume_button.draw(game_surface)
        menu_button.draw(game_surface)
        
        # Draw tips
        tips = [
            "TIP: Keep moving to avoid enemy fire",
            "TIP: Collect power-ups for temporary boosts",
            "TIP: Higher combos give more points",
            "TIP: Use coins to upgrade your ship"
        ]
        
        for i, tip in enumerate(tips):
            tip_text = FONT_SMALL.render(tip, True, CYBER_BLUE)
            game_surface.blit(tip_text, (WIDTH//2 - tip_text.get_width()//2, 400 + i * 25))
    
    # Apply screen shake if needed
    if screen_shake > 0:
        SCREEN.blit(game_surface, (int(shake_offset[0]), int(shake_offset[1])))
    else:
        SCREEN.blit(game_surface, (0, 0))
    
    # Draw mouse cursor
    pygame.draw.circle(SCREEN, CYBER_BLUE, mouse_pos, 8, 2)
    pygame.draw.circle(SCREEN, NEON_WHITE, mouse_pos, 4)
    
    # Update display
    pygame.display.flip()

# Clean up
save_data.save()
pygame.quit()
sys.exit()

