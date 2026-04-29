"""
╔══════════════════════════════════════════════════════════════╗
║          ULTRA SNAKE - Jeu Snake Complet en Python           ║
║          Auteur: Claude (Anthropic)                          ║
║          Version: 2.0 ULTRA                                  ║
╚══════════════════════════════════════════════════════════════╝
Features:
  - 10 Skins déblocables (serpent + nourriture)
  - Effets de particules et animations fluides
  - Système de niveaux avec vitesse progressive
  - Power-ups spéciaux (vitesse, double points, invincibilité)
  - Effets sonores (bip, miam, game over)
  - Highscore sauvegardé localement
  - Écran d'accueil / pause / game over animé
  - Grille animée en fond
  - Combo multiplier
  - Boss mode (obstacles mouvants)
"""

import pygame
import sys
import random
import json
import os
import math
import time

# ─── INITIALISATION PYGAME ────────────────────────────────────────────────────
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SOUND_ENABLED = True
except:
    SOUND_ENABLED = False  # Pas de son si pas de périphérique audio

# ─── CONSTANTES DE JEU ────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 900, 700          # Taille de la fenêtre
GRID_SIZE = 20                          # Taille de chaque cellule de la grille
GRID_W = (SCREEN_W - 200) // GRID_SIZE # Largeur de la grille en cellules
GRID_H = SCREEN_H // GRID_SIZE          # Hauteur de la grille en cellules
GRID_OFFSET_X = 0                       # Décalage X de la grille
SIDEBAR_W = 200                         # Largeur du panneau latéral
FPS = 60                                # Images par seconde
SAVE_FILE = "snake_save.json"           # Fichier de sauvegarde

# ─── INTERPOLATION FLUIDE ─────────────────────────────────────────────────────
# Le serpent se déplace case par case logiquement, mais visuellement
# on interpole sa position pixel par pixel entre l'ancienne et la nouvelle case.
# t_interp va de 0.0 à 1.0 sur chaque intervalle de déplacement.

# ─── COULEURS ─────────────────────────────────────────────────────────────────
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_BG     = (8,   12,  20)
GRID_COLOR  = (15,  22,  35)
NEON_GREEN  = (0,   255, 100)
NEON_BLUE   = (0,   180, 255)
NEON_PINK   = (255, 0,   180)
NEON_YELLOW = (255, 220, 0)
NEON_ORANGE = (255, 100, 0)
NEON_PURPLE = (180, 0,   255)
NEON_CYAN   = (0,   255, 220)
RED         = (220, 40,  40)
GOLD        = (255, 200, 0)
SILVER      = (180, 180, 200)

# ─── DÉFINITION DES SKINS ─────────────────────────────────────────────────────
# Chaque skin a : nom, couleur tête, couleur corps, couleur nourriture, description
SKINS = {
    "Classique":     {"head": NEON_GREEN,  "body": (0, 200, 80),   "food": RED,         "glow": NEON_GREEN,  "unlock": 0,    "desc": "Le serpent original"},
    "Océan":         {"head": NEON_BLUE,   "body": (0, 130, 200),  "food": NEON_YELLOW, "glow": NEON_BLUE,   "unlock": 10,   "desc": "Débloqué à 10 points"},
    "Plasma":        {"head": NEON_PINK,   "body": (200, 0, 150),  "food": NEON_CYAN,   "glow": NEON_PINK,   "unlock": 25,   "desc": "Débloqué à 25 points"},
    "Solaire":       {"head": NEON_ORANGE, "body": (200, 80, 0),   "food": NEON_PURPLE, "glow": NEON_ORANGE, "unlock": 50,   "desc": "Débloqué à 50 points"},
    "Fantôme":       {"head": (200,200,220),"body":(140,140,165),  "food": WHITE,       "glow": WHITE,       "unlock": 75,   "desc": "Débloqué à 75 points"},
    "Infernal":      {"head": RED,         "body": (150, 20, 20),  "food": NEON_ORANGE, "glow": RED,         "unlock": 100,  "desc": "Débloqué à 100 points"},
    "Royale":        {"head": GOLD,        "body": (200, 155, 0),  "food": WHITE,       "glow": GOLD,        "unlock": 150,  "desc": "Débloqué à 150 points"},
    "Cristal":       {"head": NEON_CYAN,   "body": (0, 200, 180),  "food": NEON_BLUE,   "glow": NEON_CYAN,   "unlock": 200,  "desc": "Débloqué à 200 points"},
    "Arc-en-ciel":   {"head": NEON_PINK,   "body": None,           "food": NEON_YELLOW, "glow": NEON_PURPLE, "unlock": 300,  "desc": "Débloqué à 300 pts! RARE"},
    "Légendaire":    {"head": GOLD,        "body": None,           "food": GOLD,        "glow": GOLD,        "unlock": 500,  "desc": "LÉGENDAIRE - 500 pts!!"},
}
SKIN_NAMES = list(SKINS.keys())

# ─── GÉNÉRATEUR DE SON PROCÉDURAL ────────────────────────────────────────────
def generate_beep(freq=440, duration=0.05, volume=0.3):
    """Génère un son bip simple avec numpy-like en pur Python."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = bytearray(n_samples * 2)
    for i in range(n_samples):
        t = i / sample_rate
        wave = math.sin(2 * math.pi * freq * t)
        # Envelope pour éviter les clics
        env = min(1.0, min(i / 200, (n_samples - i) / 200))
        val = int(wave * env * volume * 32767)
        val = max(-32768, min(32767, val))
        buf[i*2]     = val & 0xFF
        buf[i*2 + 1] = (val >> 8) & 0xFF
    sound = pygame.sndarray.make_sound(
        pygame.array.array('h', [int.from_bytes(buf[i:i+2], 'little', signed=True) for i in range(0, len(buf), 2)])
        if hasattr(pygame, 'array') else None
    )
    return sound

# Méthode alternative pour générer des sons sans numpy
def make_sound_beep(freq=440, duration=0.08, vol=0.4):
    """Génère un son bip avec pygame mixer."""
    try:
        sample_rate = 44100
        n = int(sample_rate * duration)
        # Buffer stéréo
        buf = []
        for i in range(n):
            t = i / sample_rate
            v = math.sin(2 * math.pi * freq * t)
            env = min(1.0, min(i/100, (n-i)/100))
            s = int(v * env * vol * 32767)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)  # canal droit = canal gauche
        import array as arr
        sound_arr = arr.array('h', buf)
        sound = pygame.sndarray.make_sound(
            pygame.surfarray.make_surface([[0]]) if False else None
        )
    except:
        return None

# Sons générés proceduralement via oscillateurs
class SoundEngine:
    """Moteur sonore procédural - génère tous les sons du jeu."""
    def __init__(self):
        self.sounds = {}
        self._generate_sounds()

    def _make_tone(self, freq, duration, vol=0.4, wave_type='sine', fade=True):
        """Crée un buffer sonore pour une tonalité donnée."""
        import array as arr
        sr = 44100
        n = int(sr * duration)
        buf = arr.array('h')
        for i in range(n):
            t = i / sr
            if wave_type == 'sine':
                v = math.sin(2 * math.pi * freq * t)
            elif wave_type == 'square':
                v = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
                v *= 0.5  # Carré plus fort, on réduit
            elif wave_type == 'sawtooth':
                v = 2 * (t * freq - math.floor(t * freq + 0.5))
            else:
                v = math.sin(2 * math.pi * freq * t)
            # Envelope
            if fade:
                env = min(1.0, min(i/200, (n-i)/200))
            else:
                env = min(1.0, i/200)
            s = int(v * env * vol * 32767)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)  # Stéréo
        try:
            snd = pygame.sndarray.make_sound(pygame.surfarray.map_array(
                pygame.Surface((1,1)), [[0]]
            ))
        except:
            pass
        # Méthode directe
        raw = bytes(buf)
        return pygame.mixer.Sound(buffer=raw)

    def _generate_sounds(self):
        """Génère tous les sons du jeu."""
        try:
            # Son de manger (bip montant)
            self.sounds['eat']      = self._make_tone(523, 0.08, 0.3, 'sine')
            # Son de power-up (accord)
            self.sounds['powerup']  = self._make_tone(880, 0.15, 0.4, 'sine')
            # Son de game over (note descendante)
            self.sounds['gameover'] = self._make_tone(200, 0.4, 0.5, 'square')
            # Son de niveau (accord joyeux)
            self.sounds['levelup']  = self._make_tone(660, 0.2, 0.4, 'sine')
            # Son de combo
            self.sounds['combo']    = self._make_tone(1046, 0.1, 0.35, 'sine')
            # Son de déplacement (très discret)
            self.sounds['move']     = self._make_tone(100, 0.02, 0.05, 'sine')
        except Exception as e:
            print(f"Erreur son: {e}")
            self.sounds = {}

    def play(self, name):
        """Joue un son par nom."""
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except:
                pass


# ─── SYSTÈME DE PARTICULES ────────────────────────────────────────────────────
class Particle:
    """Une particule individuelle pour les effets visuels."""
    def __init__(self, x, y, color, vel_x=None, vel_y=None, life=None, size=None):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = vel_x if vel_x is not None else random.uniform(-3, 3)
        self.vel_y = vel_y if vel_y is not None else random.uniform(-4, -1)
        self.life = life if life is not None else random.randint(20, 50)
        self.max_life = self.life
        self.size = size if size is not None else random.randint(2, 6)

    def update(self):
        """Met à jour la position et durée de vie de la particule."""
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.15  # Gravité légère
        self.vel_x *= 0.98  # Friction air
        self.life -= 1

    def draw(self, surface):
        """Dessine la particule avec fondu alpha."""
        alpha = int(255 * (self.life / self.max_life))
        r, g, b = self.color[0], self.color[1], self.color[2]
        # Crée une surface temporaire pour l'alpha
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, alpha), (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

    @property
    def alive(self):
        return self.life > 0


class ParticleSystem:
    """Gestionnaire de toutes les particules actives."""
    def __init__(self):
        self.particles = []

    def emit_eat(self, x, y, color):
        """Explosion de particules quand le serpent mange."""
        for _ in range(20):
            self.particles.append(Particle(x, y, color))
        # Quelques étincelles plus rapides
        for _ in range(8):
            self.particles.append(Particle(
                x, y, WHITE,
                vel_x=random.uniform(-6, 6),
                vel_y=random.uniform(-7, -2),
                life=25, size=3
            ))

    def emit_trail(self, x, y, color):
        """Traînée derrière le serpent."""
        for _ in range(2):
            self.particles.append(Particle(
                x, y, color,
                vel_x=random.uniform(-0.5, 0.5),
                vel_y=random.uniform(-0.5, 0.5),
                life=random.randint(8, 15),
                size=random.randint(1, 3)
            ))

    def emit_death(self, snake_body, color):
        """Explosion de mort pour chaque segment du serpent."""
        for seg in snake_body[:30]:  # Max 30 segments pour éviter le lag
            cx = seg[0] * GRID_SIZE + GRID_SIZE // 2
            cy = seg[1] * GRID_SIZE + GRID_SIZE // 2
            for _ in range(5):
                self.particles.append(Particle(cx, cy, color,
                    vel_x=random.uniform(-5, 5),
                    vel_y=random.uniform(-6, 2),
                    life=random.randint(30, 60)
                ))

    def emit_powerup(self, x, y):
        """Spirale de particules pour les power-ups."""
        for i in range(30):
            angle = (i / 30) * 2 * math.pi
            speed = random.uniform(2, 5)
            self.particles.append(Particle(
                x, y,
                random.choice([NEON_YELLOW, NEON_PINK, NEON_CYAN, WHITE]),
                vel_x=math.cos(angle) * speed,
                vel_y=math.sin(angle) * speed,
                life=40, size=4
            ))

    def update(self):
        """Met à jour toutes les particules et retire les mortes."""
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

    def draw(self, surface):
        """Dessine toutes les particules."""
        for p in self.particles:
            p.draw(surface)


# ─── POWER-UPS ─────────────────────────────────────────────────────────────────
class PowerUp:
    """Représente un power-up sur la grille."""
    TYPES = {
        'speed':       {'color': NEON_YELLOW, 'symbol': '⚡', 'duration': 5,  'desc': 'VITESSE!'},
        'slow':        {'color': NEON_BLUE,   'symbol': '❄', 'duration': 5,  'desc': 'LENT!'},
        'double':      {'color': GOLD,        'symbol': '×2', 'duration': 8,  'desc': 'DOUBLE!'},
        'invincible':  {'color': NEON_PINK,   'symbol': '★', 'duration': 4,  'desc': 'INVINCIBLE!'},
        'shrink':      {'color': NEON_CYAN,   'symbol': '↓', 'duration': 0,  'desc': '-5 SEGMENTS!'},
    }

    def __init__(self, x, y, ptype=None):
        self.x = x
        self.y = y
        self.type = ptype or random.choice(list(self.TYPES.keys()))
        self.info = self.TYPES[self.type]
        self.timer = 0        # Pour l'animation de pulsation
        self.lifetime = 300   # Disparaît après 300 frames si non ramassé
        self.alive = True

    def update(self):
        """Met à jour l'animation et durée de vie."""
        self.timer += 1
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        """Dessine le power-up avec animation pulsante."""
        cx = self.x * GRID_SIZE + GRID_SIZE // 2
        cy = self.y * GRID_SIZE + GRID_SIZE // 2
        pulse = abs(math.sin(self.timer * 0.1)) * 4
        radius = GRID_SIZE // 2 + int(pulse)
        color = self.info['color']

        # Halo externe
        s = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
        alpha = int(60 + 40 * abs(math.sin(self.timer * 0.08)))
        pygame.draw.circle(s, (*color, alpha), (radius*2, radius*2), radius*2)
        surface.blit(s, (cx - radius*2, cy - radius*2))

        # Corps du power-up
        pygame.draw.circle(surface, color, (cx, cy), radius)
        pygame.draw.circle(surface, WHITE, (cx, cy), radius - 2, 2)

        # Icône (lettre)
        font = pygame.font.SysFont('Arial', 11, bold=True)
        txt = font.render(self.info['symbol'], True, BLACK)
        surface.blit(txt, txt.get_rect(center=(cx, cy)))


# ─── OBSTACLE MOBILE (BOSS MODE) ──────────────────────────────────────────────
class MovingObstacle:
    """Obstacle mobile qui apparaît aux niveaux élevés."""
    def __init__(self, grid_w, grid_h):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.x = random.randint(2, grid_w - 3)
        self.y = random.randint(2, grid_h - 3)
        self.dx = random.choice([-1, 1])
        self.dy = 0
        self.move_timer = 0
        self.move_interval = 15  # Se déplace toutes les 15 frames
        self.length = random.randint(3, 6)  # Longueur de l'obstacle
        self.color = RED
        self.angle = 0  # Pour animation

    def update(self):
        """Déplace l'obstacle selon sa trajectoire."""
        self.move_timer += 1
        self.angle += 3
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            self.x += self.dx
            self.y += self.dy
            # Rebondit sur les bords
            if self.x <= 0 or self.x >= self.grid_w - 1:
                self.dx *= -1
            if self.y <= 0 or self.y >= self.grid_h - 1:
                self.dy *= -1

    def get_cells(self):
        """Retourne toutes les cellules occupées par l'obstacle."""
        cells = []
        for i in range(self.length):
            cells.append((self.x + i * self.dx, self.y + i * self.dy))
        return cells

    def draw(self, surface):
        """Dessine l'obstacle avec effet de flamme."""
        for i, (cx, cy) in enumerate(self.get_cells()):
            px = cx * GRID_SIZE
            py = cy * GRID_SIZE
            # Gradient rouge -> orange
            ratio = i / max(1, self.length - 1)
            r = 220
            g = int(40 + ratio * 80)
            b = 0
            color = (r, g, b)
            rect = pygame.Rect(px + 2, py + 2, GRID_SIZE - 4, GRID_SIZE - 4)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            # Effet lumineux
            pygame.draw.rect(surface, (255, 100, 0), rect, 1, border_radius=4)


# ─── SAUVEGARDE / CHARGEMENT ──────────────────────────────────────────────────
class SaveManager:
    """Gère la sauvegarde et le chargement des données de progression."""
    def __init__(self):
        self.data = {
            "highscore": 0,
            "total_games": 0,
            "total_food": 0,
            "unlocked_skins": ["Classique"],
            "selected_skin": "Classique",
            "max_level": 1,
        }
        self.load()

    def load(self):
        """Charge les données depuis le fichier JSON."""
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
        except Exception as e:
            print(f"Erreur chargement: {e}")

    def save(self):
        """Sauvegarde les données dans le fichier JSON."""
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde: {e}")

    def check_unlocks(self, score):
        """Vérifie et débloque les nouveaux skins selon le score."""
        newly_unlocked = []
        for name, skin in SKINS.items():
            if skin['unlock'] <= score and name not in self.data['unlocked_skins']:
                self.data['unlocked_skins'].append(name)
                newly_unlocked.append(name)
        return newly_unlocked

    def update_highscore(self, score):
        """Met à jour le meilleur score si battu."""
        if score > self.data['highscore']:
            self.data['highscore'] = score
            return True
        return False


# ─── SERPENT ──────────────────────────────────────────────────────────────────
class Snake:
    """Le serpent du joueur avec toutes ses propriétés."""
    def __init__(self):
        # Position initiale au centre de la grille
        start_x = GRID_W // 2
        start_y = GRID_H // 2
        self.body = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = (1, 0)       # Direction actuelle
        self.next_dir = (1, 0)        # Prochaine direction (évite les inversions)
        self.grew = False             # Flag: le serpent a-t-il grandi ce tour?
        self.alive = True

        # ── INTERPOLATION FLUIDE ──────────────────────────────────────────────
        # prev_body = positions des segments AVANT le dernier déplacement logique
        # t_interp  = progression 0.0->1.0 entre prev_body et body
        # Chaque frame, t_interp avance de (1 / interval) pour arriver à 1.0
        # exactement au moment du prochain déplacement logique.
        # Le dessin calcule la position pixel = lerp(prev, curr, t_interp)
        self.prev_body = list(self.body)   # Sauvegarde des positions précédentes
        self.t_interp  = 1.0              # Commence à 1.0 (pas d'animation initiale)

        # Animation
        self.head_angle = 0           # Angle de rotation visuelle de la tête
        self.eye_blink = 0            # Compteur de clignement des yeux
        # Effets actifs
        self.speed_boost = 0          # Frames restantes de boost de vitesse
        self.slow_effect = 0          # Frames restantes de ralentissement
        self.invincible = 0           # Frames restantes d'invincibilité
        self.double_points = 0        # Frames restantes de double points
        self.rainbow_timer = 0        # Pour l'animation arc-en-ciel

    def set_direction(self, dx, dy):
        """Change la direction en empêchant le demi-tour."""
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.next_dir = (dx, dy)

    def move(self):
        """Déplace le serpent d'une case dans la direction courante."""
        # Sauvegarde les positions actuelles AVANT de bouger
        # pour que l'interpolation parte de là
        self.prev_body = list(self.body)
        self.t_interp  = 0.0   # Repart de 0 : début de la transition

        self.direction = self.next_dir
        head_x, head_y = self.body[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        self.body.insert(0, new_head)
        if not self.grew:
            self.body.pop()
        else:
            self.grew = False
        
        # Aligne prev_body sur la même longueur que body
        while len(self.prev_body) < len(self.body):
            self.prev_body.append(self.prev_body[-1])
        while len(self.prev_body) > len(self.body):
            self.prev_body.pop()

    def grow(self):
        """Fait grandir le serpent d'un segment."""
        self.grew = True

    def shrink(self, amount=5):
        """Réduit la taille du serpent (power-up shrink)."""
        for _ in range(min(amount, len(self.body) - 3)):
            self.body.pop()

    def check_collision_wall(self):
        """Vérifie si la tête touche un mur."""
        hx, hy = self.body[0]
        return hx < 0 or hx >= GRID_W or hy < 0 or hy >= GRID_H

    def check_collision_self(self):
        """Vérifie si la tête touche le corps."""
        return self.body[0] in self.body[1:]

    def update_effects(self):
        """Décrémente les compteurs d'effets actifs."""
        if self.speed_boost > 0:    self.speed_boost -= 1
        if self.slow_effect > 0:    self.slow_effect -= 1
        if self.invincible > 0:     self.invincible -= 1
        if self.double_points > 0:  self.double_points -= 1
        self.eye_blink = (self.eye_blink + 1) % 120
        self.rainbow_timer = (self.rainbow_timer + 3) % 360

    def get_move_interval(self, base_interval):
        """Calcule l'intervalle de déplacement en fonction des effets."""
        interval = base_interval
        if self.speed_boost > 0:
            interval = max(3, interval // 2)
        if self.slow_effect > 0:
            interval = min(30, interval * 2)
        return interval

    def get_segment_color(self, index, skin):
        """Calcule la couleur d'un segment en fonction du skin et de l'index."""
        if skin['body'] is None:
            # Mode arc-en-ciel : couleur basée sur position + index
            hue = (self.rainbow_timer + index * 15) % 360
            return hsv_to_rgb(hue, 1.0, 1.0)
        # Gradient tête -> queue
        ratio = index / max(1, len(self.body) - 1)
        h = tuple(int(skin['head'][i] * (1 - ratio * 0.5) + skin['body'][i] * ratio * 0.5) for i in range(3))
        return h

    def get_interp_pos(self, i):
        """Retourne la position pixel interpolée du segment i.
        Interpole linéairement entre prev_body[i] et body[i] selon t_interp.
        Cela donne un glissement fluide entre chaque case."""
        t = self.t_interp
        # Easing : accélération douce avec smoothstep (t*t*(3-2t))
        t = t * t * (3 - 2 * t)
        if i < len(self.prev_body):
            px, py = self.prev_body[i]
        else:
            px, py = self.body[i]
        cx, cy = self.body[i]
        ix = px + (cx - px) * t
        iy = py + (cy - py) * t
        return ix * GRID_SIZE, iy * GRID_SIZE

    def draw(self, surface, skin, particles):
        """Dessine le serpent complet avec tous les effets visuels."""
        glow_color = skin['glow']

        # ── Dessiner de la queue vers la tête (tête au-dessus)
        for i in range(len(self.body) - 1, -1, -1):
            # ── Position interpolée (fluide) au lieu de la position logique brute
            x, y = self.get_interp_pos(i)
            x, y = int(x), int(y)
            color = self.get_segment_color(i, skin)
            seg = self.body[i]  # Gardé pour compatibilité (collisions etc.)

            # Effet d'invincibilité (clignotement + halo)
            if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
                color = WHITE

            # Segment arrondi
            rect = pygame.Rect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2)

            if i == 0:
                # ── TÊTE ──
                # Halo lumineux
                draw_glow(surface, x + GRID_SIZE//2, y + GRID_SIZE//2,
                          GRID_SIZE, glow_color, intensity=80 if self.invincible > 0 else 40)
                pygame.draw.rect(surface, color, rect, border_radius=7)
                # Reflet brillant
                pygame.draw.rect(surface, tuple(min(255, c + 60) for c in color),
                                 pygame.Rect(x + 3, y + 3, GRID_SIZE//3, GRID_SIZE//3), border_radius=3)

                # Yeux
                dx, dy = self.direction
                eye_offset = 4
                if dx == 1:   eyes = [(x+13, y+4), (x+13, y+12)]
                elif dx == -1: eyes = [(x+3, y+4), (x+3, y+12)]
                elif dy == -1: eyes = [(x+4, y+3), (x+12, y+3)]
                else:          eyes = [(x+4, y+13), (x+12, y+13)]

                for ex, ey in eyes:
                    pygame.draw.circle(surface, WHITE, (ex, ey), 3)
                    # Pupille qui cligne
                    pupil_size = 1 if (40 <= self.eye_blink <= 44) else 2
                    pygame.draw.circle(surface, BLACK, (ex, ey), pupil_size)

                # Langue (clignote)
                if (self.eye_blink // 20) % 2 == 0:
                    tx = x + GRID_SIZE//2 + dx * (GRID_SIZE//2 + 3)
                    ty = y + GRID_SIZE//2 + dy * (GRID_SIZE//2 + 3)
                    pygame.draw.line(surface, RED, (tx, ty),
                                     (tx + dx*4, ty + dy*4), 2)
                    pygame.draw.circle(surface, RED, (tx + dx*6, ty + dy*5), 2)
                    pygame.draw.circle(surface, RED, (tx + dx*6, ty + dy*3), 2)

            else:
                # ── CORPS ──
                # Effets de traînée au skin arc-en-ciel
                if skin.get('unlock', 0) >= 300:
                    particles.emit_trail(x + GRID_SIZE//2, y + GRID_SIZE//2, color)

                # Dessin du segment avec coins arrondis
                corner = 5 if i < len(self.body) - 1 else 8
                pygame.draw.rect(surface, color, rect, border_radius=corner)

                # Ligne séparatrice entre segments (effet écailles)
                if i % 2 == 0:
                    dark = tuple(max(0, c - 30) for c in color)
                    pygame.draw.rect(surface, dark, rect, 1, border_radius=corner)


# ─── NOURRITURE ───────────────────────────────────────────────────────────────
class Food:
    """La nourriture que le serpent doit manger."""
    def __init__(self, skin_color):
        self.x = 0
        self.y = 0
        self.color = skin_color
        self.timer = 0
        self.spawn_anim = 15  # Frames d'animation d'apparition

    def spawn(self, snake_body, obstacles_cells=None):
        """Place la nourriture aléatoirement en évitant le serpent et obstacles."""
        occupied = set(snake_body)
        if obstacles_cells:
            occupied.update(obstacles_cells)
        attempts = 0
        while attempts < 1000:
            self.x = random.randint(1, GRID_W - 2)
            self.y = random.randint(1, GRID_H - 2)
            if (self.x, self.y) not in occupied:
                self.spawn_anim = 15
                return
            attempts += 1

    def update(self):
        """Met à jour l'animation."""
        self.timer += 1
        if self.spawn_anim > 0:
            self.spawn_anim -= 1

    def draw(self, surface):
        """Dessine la nourriture avec animations pulse et brillance."""
        cx = self.x * GRID_SIZE + GRID_SIZE // 2
        cy = self.y * GRID_SIZE + GRID_SIZE // 2

        # Animation d'apparition
        if self.spawn_anim > 0:
            scale = 1 - (self.spawn_anim / 15) * 0.5
        else:
            # Pulsation continue
            scale = 1.0 + 0.15 * math.sin(self.timer * 0.12)

        radius = int((GRID_SIZE // 2 - 2) * scale)
        if radius <= 0:
            return

        # Halo lumineux
        draw_glow(surface, cx, cy, radius * 2, self.color, intensity=70)

        # Corps de la nourriture (cercle principal)
        pygame.draw.circle(surface, self.color, (cx, cy), radius)

        # Reflet brillant
        pygame.draw.circle(surface, tuple(min(255, c + 80) for c in self.color),
                           (cx - radius//3, cy - radius//3), radius//3)

        # Étoile scintillante
        if (self.timer // 15) % 4 == 0:
            for angle in range(0, 360, 72):
                rad = math.radians(angle + self.timer * 3)
                ex = int(cx + math.cos(rad) * (radius + 4))
                ey = int(cy + math.sin(rad) * (radius + 4))
                pygame.draw.circle(surface, WHITE, (ex, ey), 2)


# ─── FONCTIONS UTILITAIRES ────────────────────────────────────────────────────
def hsv_to_rgb(h, s, v):
    """Convertit HSV en RGB pour l'effet arc-en-ciel."""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:          r, g, b = c, 0, x
    return (int((r+m)*255), int((g+m)*255), int((b+m)*255))

def draw_glow(surface, cx, cy, radius, color, intensity=50):
    """Dessine un halo lumineux autour d'un point."""
    glow_surf = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
    for r in range(radius*2, 0, -4):
        alpha = int(intensity * (r / (radius*2)) ** 2)
        pygame.draw.circle(glow_surf, (*color, alpha),
                           (radius*2, radius*2), r)
    surface.blit(glow_surf, (cx - radius*2, cy - radius*2))

def draw_grid(surface):
    """Dessine la grille de fond avec effet lumineux subtil."""
    for x in range(0, GRID_W * GRID_SIZE, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, GRID_H * GRID_SIZE))
    for y in range(0, GRID_H * GRID_SIZE, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (GRID_W * GRID_SIZE, y))

def draw_text_shadow(surface, text, font, color, x, y, shadow_color=(0,0,0), offset=2):
    """Dessine du texte avec une ombre portée."""
    shadow = font.render(text, True, shadow_color)
    surface.blit(shadow, (x + offset, y + offset))
    main = font.render(text, True, color)
    surface.blit(main, (x, y))

def draw_glowing_text(surface, text, font, color, cx, cy):
    """Dessine du texte avec effet lumineux centré."""
    # Halo
    glow_font = font
    for offset in [(2,2), (-2,2), (2,-2), (-2,-2), (0,3), (3,0)]:
        glow_surf = glow_font.render(text, True, tuple(c//3 for c in color))
        rect = glow_surf.get_rect(center=(cx + offset[0], cy + offset[1]))
        surface.blit(glow_surf, rect)
    # Texte principal
    txt_surf = font.render(text, True, color)
    rect = txt_surf.get_rect(center=(cx, cy))
    surface.blit(txt_surf, rect)


# ─── BARRE DE SCORE / HUD ──────────────────────────────────────────────────────
class HUD:
    """Affichage tête haute avec score, niveau, effets actifs."""
    def __init__(self, save_manager):
        self.save = save_manager
        self.font_big   = pygame.font.SysFont('Consolas', 28, bold=True)
        self.font_med   = pygame.font.SysFont('Consolas', 18, bold=True)
        self.font_small = pygame.font.SysFont('Consolas', 14)
        self.score_anim = 0   # Animation du score qui monte
        self.displayed_score = 0
        self.combo_display = 0  # Durée d'affichage du combo

    def draw(self, surface, score, level, length, combo, effects, skin_name):
        """Dessine le panneau latéral complet."""
        # Panneau latéral
        sidebar_rect = pygame.Rect(GRID_W * GRID_SIZE, 0, SIDEBAR_W, SCREEN_H)
        pygame.draw.rect(surface, (12, 18, 30), sidebar_rect)
        pygame.draw.line(surface, NEON_BLUE, (GRID_W * GRID_SIZE, 0),
                         (GRID_W * GRID_SIZE, SCREEN_H), 2)

        sx = GRID_W * GRID_SIZE + 10
        sy = 15

        # ── TITRE
        draw_glowing_text(surface, "ULTRA", self.font_big, NEON_CYAN, GRID_W * GRID_SIZE + SIDEBAR_W//2, sy + 10)
        draw_glowing_text(surface, "SNAKE", self.font_big, NEON_GREEN, GRID_W * GRID_SIZE + SIDEBAR_W//2, sy + 38)

        sy += 70
        pygame.draw.line(surface, NEON_GREEN, (sx - 5, sy), (sx + SIDEBAR_W - 15, sy), 1)
        sy += 10

        # ── SCORE avec animation
        self.displayed_score += (score - self.displayed_score) * 0.2
        score_color = GOLD if score >= self.save.data['highscore'] and score > 0 else WHITE
        label = self.font_small.render("SCORE", True, NEON_GREEN)
        surface.blit(label, (sx, sy))
        score_txt = self.font_big.render(str(int(self.displayed_score)), True, score_color)
        surface.blit(score_txt, (sx, sy + 18))
        if score > 0 and score >= self.save.data['highscore']:
            best = self.font_small.render("✦ RECORD!", True, GOLD)
            surface.blit(best, (sx, sy + 48))

        sy += 65

        # ── MEILLEUR SCORE
        hs_label = self.font_small.render("MEILLEUR", True, SILVER)
        surface.blit(hs_label, (sx, sy))
        hs_txt = self.font_med.render(str(self.save.data['highscore']), True, SILVER)
        surface.blit(hs_txt, (sx, sy + 16))

        sy += 45
        pygame.draw.line(surface, (30, 45, 70), (sx - 5, sy), (sx + SIDEBAR_W - 15, sy), 1)
        sy += 10

        # ── NIVEAU
        lv_label = self.font_small.render("NIVEAU", True, NEON_YELLOW)
        surface.blit(lv_label, (sx, sy))
        lv_txt = self.font_big.render(str(level), True, NEON_YELLOW)
        surface.blit(lv_txt, (sx, sy + 16))
        # Barre de progression du niveau (10 points par niveau)
        progress = (score % 10) / 10.0
        bar_w = SIDEBAR_W - 25
        pygame.draw.rect(surface, (30, 45, 70), (sx, sy + 46, bar_w, 8), border_radius=4)
        pygame.draw.rect(surface, NEON_YELLOW, (sx, sy + 46, int(bar_w * progress), 8), border_radius=4)

        sy += 65

        # ── LONGUEUR
        len_label = self.font_small.render("LONGUEUR", True, NEON_BLUE)
        surface.blit(len_label, (sx, sy))
        len_txt = self.font_med.render(str(length), True, NEON_BLUE)
        surface.blit(len_txt, (sx, sy + 16))

        sy += 40
        pygame.draw.line(surface, (30, 45, 70), (sx - 5, sy), (sx + SIDEBAR_W - 15, sy), 1)
        sy += 10

        # ── COMBO
        if combo > 1:
            combo_color = NEON_PINK if combo >= 5 else NEON_ORANGE
            self.combo_display = 60
            combo_txt = self.font_big.render(f"×{combo}", True, combo_color)
            surface.blit(combo_txt, (sx, sy))
            combo_label = self.font_small.render("COMBO!", True, combo_color)
            surface.blit(combo_label, (sx + combo_txt.get_width() + 5, sy + 8))
            sy += 45

        # ── EFFETS ACTIFS
        if any(effects.values()):
            eff_label = self.font_small.render("EFFETS:", True, NEON_CYAN)
            surface.blit(eff_label, (sx, sy))
            sy += 18
            effect_icons = {
                'speed':      ('⚡RAPIDE', NEON_YELLOW),
                'slow':       ('❄LENT',   NEON_BLUE),
                'double':     ('×2 PTS',  GOLD),
                'invincible': ('★INVIC.', NEON_PINK),
            }
            for key, (label, color) in effect_icons.items():
                if effects.get(key, 0) > 0:
                    # Barre de durée
                    max_dur = {'speed': 300, 'slow': 300, 'double': 480, 'invincible': 240}
                    ratio = effects[key] / max_dur.get(key, 300)
                    bar_w2 = SIDEBAR_W - 25
                    pygame.draw.rect(surface, (20, 30, 50), (sx, sy + 14, bar_w2, 5))
                    pygame.draw.rect(surface, color, (sx, sy + 14, int(bar_w2 * ratio), 5), border_radius=2)
                    eff_txt = self.font_small.render(label, True, color)
                    surface.blit(eff_txt, (sx, sy))
                    sy += 22

        # ── SKIN ACTIF (en bas)
        skin_y = SCREEN_H - 70
        pygame.draw.line(surface, (30, 45, 70), (sx - 5, skin_y - 5),
                         (sx + SIDEBAR_W - 15, skin_y - 5), 1)
        skin_label = self.font_small.render("SKIN ACTIF", True, (100, 120, 160))
        surface.blit(skin_label, (sx, skin_y))
        skin_color = SKINS.get(skin_name, SKINS['Classique'])['glow']
        skin_txt = self.font_small.render(skin_name, True, skin_color)
        surface.blit(skin_txt, (sx, skin_y + 16))
        # Contrôles
        ctrl = self.font_small.render("P:Pause  ESC:Menu", True, (60, 80, 110))
        surface.blit(ctrl, (sx, SCREEN_H - 20))


# ─── ÉCRANS DE JEU ────────────────────────────────────────────────────────────
class MenuScreen:
    """Écran principal du menu avec animations."""
    def __init__(self, save_manager):
        self.save = save_manager
        self.font_title = pygame.font.SysFont('Consolas', 60, bold=True)
        self.font_sub   = pygame.font.SysFont('Consolas', 22, bold=True)
        self.font_med   = pygame.font.SysFont('Consolas', 18)
        self.font_small = pygame.font.SysFont('Consolas', 14)
        self.timer = 0
        self.selected = 0  # Option sélectionnée
        self.options = ["JOUER", "SKINS", "SCORES", "QUITTER"]
        # Serpent décoratif animé en arrière-plan
        self.deco_snake = [(5 + i, 5) for i in range(8)]
        self.deco_dir = (1, 0)
        self.deco_timer = 0

    def update(self):
        """Met à jour les animations du menu."""
        self.timer += 1
        # Déplace le serpent décoratif
        self.deco_timer += 1
        if self.deco_timer >= 8:
            self.deco_timer = 0
            hx, hy = self.deco_snake[0]
            nhx, nhy = hx + self.deco_dir[0], hy + self.deco_dir[1]
            if nhx < 0 or nhx >= GRID_W or nhy < 0 or nhy >= GRID_H:
                # Tourne
                possible = [(1,0),(-1,0),(0,1),(0,-1)]
                possible.remove((-self.deco_dir[0], -self.deco_dir[1]))
                self.deco_dir = random.choice(possible)
                nhx, nhy = hx + self.deco_dir[0], hy + self.deco_dir[1]
                nhx = max(0, min(GRID_W-1, nhx))
                nhy = max(0, min(GRID_H-1, nhy))
            self.deco_snake.insert(0, (nhx, nhy))
            if len(self.deco_snake) > 15:
                self.deco_snake.pop()

    def handle_input(self, event):
        """Gère les entrées clavier sur le menu."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected]
        return None

    def draw(self, surface):
        """Dessine l'écran du menu."""
        surface.fill(DARK_BG)
        draw_grid(surface)

        # Serpent décoratif en fond
        for i, seg in enumerate(self.deco_snake):
            ratio = i / len(self.deco_snake)
            color = hsv_to_rgb(int(self.timer * 1.5 + i * 20) % 360, 0.8, 0.6 * (1 - ratio * 0.5))
            px = seg[0] * GRID_SIZE + GRID_SIZE // 2
            py = seg[1] * GRID_SIZE + GRID_SIZE // 2
            pygame.draw.circle(surface, color, (px, py), GRID_SIZE//2 - 2)

        # Titre animé
        wave_y = int(math.sin(self.timer * 0.05) * 8)
        cx = SCREEN_W // 2

        # Ombre du titre
        for dx, dy in [(-3,3),(3,3),(-3,-3),(3,-3)]:
            shadow = self.font_title.render("ULTRA SNAKE", True, (0, 80, 0))
            rect = shadow.get_rect(center=(cx + dx, 100 + wave_y + dy))
            surface.blit(shadow, rect)

        # Lettres du titre avec couleurs arc-en-ciel
        title = "ULTRA SNAKE"
        total_w = self.font_title.size(title)[0]
        for i, ch in enumerate(title):
            hue = (self.timer * 2 + i * 25) % 360
            color = hsv_to_rgb(hue, 1.0, 1.0)
            ch_surf = self.font_title.render(ch, True, color)
            ch_x = cx - total_w // 2 + self.font_title.size(title[:i])[0]
            bounce = int(math.sin(self.timer * 0.08 + i * 0.4) * 5)
            surface.blit(ch_surf, (ch_x, 75 + wave_y + bounce))

        # Sous-titre
        sub_alpha = int(180 + 75 * math.sin(self.timer * 0.04))
        sub = self.font_sub.render("Le Snake Ultime avec Skins & Power-ups!", True,
                                    tuple(min(255, c) for c in (0, sub_alpha, sub_alpha//2)))
        surface.blit(sub, sub.get_rect(center=(cx, 155)))

        # Stats rapides
        stats_y = 195
        hs_txt = self.font_med.render(f"Meilleur score: {self.save.data['highscore']}  |  "
                                      f"Skins débloqués: {len(self.save.data['unlocked_skins'])}/{len(SKINS)}",
                                      True, SILVER)
        surface.blit(hs_txt, hs_txt.get_rect(center=(cx, stats_y)))

        # Séparateur
        sep_y = 225
        pygame.draw.line(surface, NEON_GREEN, (cx - 200, sep_y), (cx + 200, sep_y), 1)

        # Options du menu
        for i, opt in enumerate(self.options):
            is_selected = (i == self.selected)
            if is_selected:
                # Fond sélectionné
                pulse = int(30 + 20 * abs(math.sin(self.timer * 0.1)))
                sel_rect = pygame.Rect(cx - 120, 255 + i * 55 - 5, 240, 45)
                s = pygame.Surface((240, 45), pygame.SRCALPHA)
                pygame.draw.rect(s, (0, 180, 80, pulse), (0,0,240,45), border_radius=8)
                surface.blit(s, (cx - 120, 255 + i * 55 - 5))
                # Flèches
                surface.blit(self.font_sub.render("▶", True, NEON_GREEN),
                             (cx - 140, 255 + i * 55))
                surface.blit(self.font_sub.render("◀", True, NEON_GREEN),
                             (cx + 115, 255 + i * 55))
                color = WHITE
            else:
                color = (100, 140, 120)

            txt = self.font_sub.render(opt, True, color)
            surface.blit(txt, txt.get_rect(center=(cx, 275 + i * 55)))

        # Instructions
        inst = self.font_small.render("↑↓ Naviguer  |  ENTRÉE Sélectionner  |  ZQSD / Flèches pour jouer",
                                       True, (60, 90, 80))
        surface.blit(inst, inst.get_rect(center=(cx, SCREEN_H - 30)))

        # Version
        ver = self.font_small.render("v2.0 ULTRA", True, (40, 60, 50))
        surface.blit(ver, (10, SCREEN_H - 20))


class SkinSelectScreen:
    """Écran de sélection des skins."""
    def __init__(self, save_manager):
        self.save = save_manager
        self.font_big   = pygame.font.SysFont('Consolas', 32, bold=True)
        self.font_med   = pygame.font.SysFont('Consolas', 18, bold=True)
        self.font_small = pygame.font.SysFont('Consolas', 14)
        self.selected = SKIN_NAMES.index(save_manager.data.get('selected_skin', 'Classique'))
        self.timer = 0

    def handle_input(self, event):
        """Gère la navigation entre les skins."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(SKIN_NAMES)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(SKIN_NAMES)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                name = SKIN_NAMES[self.selected]
                if name in self.save.data['unlocked_skins']:
                    self.save.data['selected_skin'] = name
                    self.save.save()
                    return 'select'
            elif event.key == pygame.K_ESCAPE:
                return 'back'
        return None

    def draw(self, surface):
        """Dessine l'écran de sélection de skins."""
        self.timer += 1
        surface.fill(DARK_BG)
        draw_grid(surface)
        cx = SCREEN_W // 2

        # Titre
        draw_glowing_text(surface, "SKINS", self.font_big, NEON_CYAN, cx, 40)

        # Affiche tous les skins en grille
        cols = 5
        rows = 2
        cell_w = 150
        cell_h = 200
        start_x = cx - (cols * cell_w) // 2
        start_y = 90

        for idx, name in enumerate(SKIN_NAMES):
            col = idx % cols
            row = idx // cols
            x = start_x + col * cell_w
            y = start_y + row * cell_h
            skin = SKINS[name]
            is_selected = (idx == self.selected)
            is_unlocked = name in self.save.data['unlocked_skins']
            is_current  = (name == self.save.data.get('selected_skin'))

            # Fond de cellule
            border_color = skin['glow'] if is_selected else (30, 45, 70)
            bg_alpha = 60 if is_selected else 20
            s = pygame.Surface((cell_w - 10, cell_h - 10), pygame.SRCALPHA)
            r, g, b = border_color
            pygame.draw.rect(s, (r, g, b, bg_alpha), (0, 0, cell_w-10, cell_h-10), border_radius=10)
            if is_selected:
                pygame.draw.rect(s, (*border_color, 200), (0, 0, cell_w-10, cell_h-10), 2, border_radius=10)
            surface.blit(s, (x + 5, y + 5))

            # Aperçu du serpent (mini segments)
            preview_cx = x + cell_w // 2
            preview_cy = y + 65
            seg_size = 12
            for si in range(5):
                if skin['body'] is None:
                    # Arc-en-ciel
                    seg_color = hsv_to_rgb((self.timer * 3 + si * 40) % 360, 1.0, 1.0 if is_unlocked else 0.3)
                elif si == 0:
                    seg_color = skin['head'] if is_unlocked else (40, 40, 40)
                else:
                    base = skin['body']
                    ratio = si / 4
                    seg_color = tuple(int(skin['head'][i]*(1-ratio) + base[i]*ratio) for i in range(3)) if is_unlocked else (40,40,40)

                seg_x = preview_cx + (si - 2) * (seg_size + 2) - seg_size // 2
                seg_y = preview_cy - seg_size // 2
                pygame.draw.rect(surface, seg_color, (seg_x, seg_y, seg_size, seg_size), border_radius=3)
                if si == 0 and is_unlocked:
                    pygame.draw.circle(surface, WHITE, (seg_x + 9, seg_y + 3), 2)
                    pygame.draw.circle(surface, WHITE, (seg_x + 9, seg_y + 9), 2)

            # Nourriture preview
            food_color = skin['food'] if is_unlocked else (40, 40, 40)
            pygame.draw.circle(surface, food_color, (preview_cx + 45, preview_cy), 6)

            # Nom du skin
            name_color = skin['glow'] if is_unlocked else (60, 60, 60)
            name_surf = self.font_small.render(name, True, name_color)
            surface.blit(name_surf, name_surf.get_rect(center=(x + cell_w//2, y + 100)))

            # Statut débloqué / verrouillé
            if is_unlocked:
                if is_current:
                    status = self.font_small.render("✦ ACTIF", True, GOLD)
                else:
                    status = self.font_small.render("DÉBLOQUÉ", True, NEON_GREEN)
            else:
                pts = self.font_small.render(f"🔒 {skin['unlock']} pts", True, (120, 80, 80))
                status = pts
            surface.blit(status, status.get_rect(center=(x + cell_w//2, y + 118)))

            # Description
            desc_surf = self.font_small.render(skin['desc'][:18], True, (80, 100, 120))
            surface.blit(desc_surf, desc_surf.get_rect(center=(x + cell_w//2, y + 140)))

        # Instructions
        inst_y = SCREEN_H - 50
        pygame.draw.line(surface, (30, 45, 70), (50, inst_y - 10), (SCREEN_W - 50, inst_y - 10), 1)
        hints = [
            "← → Naviguer   |   ENTRÉE Sélectionner   |   ESC Retour",
            f"Skin actuel: {self.save.data.get('selected_skin', 'Classique')}  |  {len(self.save.data['unlocked_skins'])}/{len(SKINS)} débloqués"
        ]
        for i, hint in enumerate(hints):
            h = self.font_small.render(hint, True, (80, 110, 100))
            surface.blit(h, h.get_rect(center=(cx, inst_y + i * 18)))


class GameOverScreen:
    """Écran de fin de partie avec animations et récap."""
    def __init__(self, save_manager):
        self.save = save_manager
        self.font_big   = pygame.font.SysFont('Consolas', 48, bold=True)
        self.font_med   = pygame.font.SysFont('Consolas', 22, bold=True)
        self.font_small = pygame.font.SysFont('Consolas', 16)
        self.timer = 0
        self.data = {}

    def set_data(self, score, level, length, new_record, newly_unlocked):
        """Définit les données à afficher sur l'écran."""
        self.data = {
            'score': score, 'level': level, 'length': length,
            'new_record': new_record, 'unlocked': newly_unlocked
        }
        self.timer = 0

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return 'restart'
            elif event.key == pygame.K_ESCAPE:
                return 'menu'
        return None

    def draw(self, surface):
        """Dessine l'écran game over."""
        self.timer += 1
        # Overlay semi-transparent
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, SCREEN_W, SCREEN_H))
        surface.blit(overlay, (0, 0))

        cx = (GRID_W * GRID_SIZE) // 2  # Centre de la zone de jeu

        # Panneau central
        panel_w, panel_h = 480, 420
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 12, 25, 220), (0, 0, panel_w, panel_h), border_radius=15)
        pygame.draw.rect(panel, RED, (0, 0, panel_w, panel_h), 2, border_radius=15)
        surface.blit(panel, (cx - panel_w//2, SCREEN_H//2 - panel_h//2))

        # Animation du titre GAME OVER
        shake_x = int(math.sin(self.timer * 0.3) * (max(0, 20 - self.timer * 0.3)))
        shake_y = int(math.cos(self.timer * 0.4) * (max(0, 15 - self.timer * 0.25)))
        hue = (self.timer * 3) % 360
        go_color = hsv_to_rgb(hue, 1.0, 1.0) if self.timer < 120 else RED
        draw_glowing_text(surface, "GAME OVER", self.font_big, go_color,
                          cx + shake_x, SCREEN_H//2 - 170 + shake_y)

        # Nouveau record !
        if self.data.get('new_record'):
            pulse = int(200 + 55 * abs(math.sin(self.timer * 0.08)))
            rec_color = (pulse, int(pulse*0.8), 0)
            draw_glowing_text(surface, "✦ NOUVEAU RECORD! ✦", self.font_med, rec_color,
                              cx, SCREEN_H//2 - 120)

        # Stats
        stats_y = SCREEN_H//2 - 85
        stats = [
            (f"Score final :  {self.data.get('score', 0)}", GOLD),
            (f"Niveau atteint : {self.data.get('level', 1)}", NEON_YELLOW),
            (f"Longueur max : {self.data.get('length', 3)}", NEON_CYAN),
            (f"Meilleur score : {self.save.data['highscore']}", SILVER),
        ]
        for i, (text, color) in enumerate(stats):
            # Animation d'apparition décalée
            appear = max(0, min(1, (self.timer - i * 8) / 20))
            if appear > 0:
                alpha = int(255 * appear)
                txt = self.font_med.render(text, True, color)
                s = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
                s.blit(txt, (0, 0))
                s.set_alpha(alpha)
                surface.blit(s, s.get_rect(center=(cx, stats_y + i * 35)))

        # Skins débloqués
        if self.data.get('unlocked'):
            unlock_y = stats_y + 160
            ul_txt = self.font_med.render("🎉 NOUVEAU SKIN DÉBLOQUÉ!", True, NEON_GREEN)
            surface.blit(ul_txt, ul_txt.get_rect(center=(cx, unlock_y)))
            for i, sk in enumerate(self.data['unlocked']):
                sk_color = SKINS[sk]['glow']
                sk_txt = self.font_small.render(f"★ {sk}", True, sk_color)
                surface.blit(sk_txt, sk_txt.get_rect(center=(cx, unlock_y + 25 + i*20)))

        # Boutons
        btn_y = SCREEN_H//2 + 165
        # REJOUER
        replay_rect = pygame.Rect(cx - 150, btn_y, 130, 40)
        pygame.draw.rect(surface, (0, 120, 60), replay_rect, border_radius=8)
        pygame.draw.rect(surface, NEON_GREEN, replay_rect, 2, border_radius=8)
        rp_txt = self.font_small.render("ENTRÉE - Rejouer", True, WHITE)
        surface.blit(rp_txt, rp_txt.get_rect(center=replay_rect.center))

        # MENU
        menu_rect = pygame.Rect(cx + 20, btn_y, 130, 40)
        pygame.draw.rect(surface, (60, 20, 20), menu_rect, border_radius=8)
        pygame.draw.rect(surface, RED, menu_rect, 2, border_radius=8)
        mn_txt = self.font_small.render("ESC - Menu", True, WHITE)
        surface.blit(mn_txt, mn_txt.get_rect(center=menu_rect.center))


# ─── ÉTAT DU JEU PRINCIPAL ────────────────────────────────────────────────────
class GameState:
    """Gère l'état complet d'une partie en cours."""
    def __init__(self, save_manager, skin_name):
        self.save = save_manager
        self.skin_name = skin_name
        self.skin = SKINS[skin_name]

        # Entités de jeu
        self.snake = Snake()
        self.particles = ParticleSystem()
        self.food = Food(self.skin['food'])
        self.food.spawn(self.snake.body)
        self.powerups = []
        self.obstacles = []

        # Score et progression
        self.score = 0
        self.level = 1
        self.combo = 0          # Nombre de nourritures consécutives sans mouvement
        self.combo_since = 0    # Frames depuis dernier combo

        # Timers
        self.move_timer = 0
        self.base_interval = 12       # Frames entre chaque déplacement
        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 350  # Spawn un power-up toutes les N frames

        # Textes flottants (score +X, combo, etc.)
        self.floating_texts = []

        # Pause
        self.paused = False
        self.pause_font = pygame.font.SysFont('Consolas', 40, bold=True)

        # Écran de notification skin débloqué
        self.unlock_notif = []
        self.notif_font = pygame.font.SysFont('Consolas', 20, bold=True)

        # Sons
        self.sound = SoundEngine()

        # HUD
        self.hud = HUD(save_manager)

    def get_base_interval(self):
        """Calcule l'intervalle de base selon le niveau."""
        # Plus le niveau est élevé, plus c'est rapide
        return max(4, self.base_interval - (self.level - 1))

    def spawn_powerup(self):
        """Génère un power-up aléatoire sur la grille."""
        occupied = set(self.snake.body) | {(self.food.x, self.food.y)}
        for existing in self.powerups:
            occupied.add((existing.x, existing.y))
        for _ in range(100):
            x = random.randint(1, GRID_W - 2)
            y = random.randint(1, GRID_H - 2)
            if (x, y) not in occupied:
                self.powerups.append(PowerUp(x, y))
                break

    def apply_powerup(self, ptype):
        """Applique l'effet d'un power-up collecté."""
        fps_dur = 60  # 1 seconde = 60 frames
        if ptype == 'speed':
            self.snake.speed_boost = 5 * fps_dur
        elif ptype == 'slow':
            self.snake.slow_effect = 5 * fps_dur
        elif ptype == 'double':
            self.snake.double_points = 8 * fps_dur
        elif ptype == 'invincible':
            self.snake.invincible = 4 * fps_dur
        elif ptype == 'shrink':
            self.snake.shrink()

    def add_floating_text(self, x, y, text, color):
        """Ajoute un texte flottant animé (ex: +10 pts)."""
        self.floating_texts.append({
            'x': x * GRID_SIZE + GRID_SIZE // 2,
            'y': y * GRID_SIZE,
            'text': text,
            'color': color,
            'life': 60,
            'vy': -1.5
        })

    def update(self):
        """Met à jour tout le jeu pour cette frame."""
        if self.paused:
            return

        # Mise à jour des effets du serpent
        self.snake.update_effects()

        # Timer de déplacement
        self.move_timer += 1
        interval = self.snake.get_move_interval(self.get_base_interval())

        # ── Avance l'interpolation fluide chaque frame ───────────────────────
        # t_interp passe de 0.0 à 1.0 sur exactement "interval" frames,
        # synchronisé avec le déplacement logique pour un glissement parfait.
        if interval > 0:
            self.snake.t_interp = min(1.0, self.snake.t_interp + 1.0 / interval)

        if self.move_timer >= interval:
            self.move_timer = 0
            self._do_move()

        # Mise à jour particules, nourriture, power-ups
        self.particles.update()
        self.food.update()

        for pu in self.powerups[:]:
            pu.update()
            if not pu.alive:
                self.powerups.remove(pu)

        for obs in self.obstacles:
            obs.update()

        # Spawn power-ups
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer >= self.powerup_spawn_interval:
            self.powerup_spawn_timer = 0
            if len(self.powerups) < 3:  # Max 3 power-ups simultanés
                self.spawn_powerup()

        # Textes flottants
        for ft in self.floating_texts[:]:
            ft['y'] += ft['vy']
            ft['life'] -= 1
            if ft['life'] <= 0:
                self.floating_texts.remove(ft)

        # Notifs skin débloqué
        for notif in self.unlock_notif[:]:
            notif['life'] -= 1
            if notif['life'] <= 0:
                self.unlock_notif.remove(notif)

    def _do_move(self):
        """Effectue un déplacement du serpent et vérifie toutes les collisions."""
        self.snake.move()
        head = self.snake.body[0]

        # Collision mur
        if self.snake.check_collision_wall():
            if self.snake.invincible <= 0:
                self._game_over()
                return

        # Collision corps
        if self.snake.check_collision_self():
            if self.snake.invincible <= 0:
                self._game_over()
                return

        # Collision obstacles
        for obs in self.obstacles:
            if head in obs.get_cells():
                if self.snake.invincible <= 0:
                    self._game_over()
                    return

        # Manger la nourriture
        if head == (self.food.x, self.food.y):
            self._eat_food()

        # Collecter un power-up
        for pu in self.powerups[:]:
            if head == (pu.x, pu.y):
                self._collect_powerup(pu)

    def _eat_food(self):
        """Gère la collecte de nourriture."""
        self.snake.grow()
        self.combo += 1
        pts = 1
        if self.snake.double_points > 0:
            pts *= 2
        if self.combo >= 3:
            pts += self.combo - 2  # Bonus combo
            if self.combo >= 5:
                self.sound.play('combo')
                self.add_floating_text(self.food.x, self.food.y,
                                       f"COMBO ×{self.combo}!", NEON_PINK)
            else:
                self.add_floating_text(self.food.x, self.food.y,
                                       f"+{pts} ×{self.combo}", NEON_ORANGE)
        else:
            self.add_floating_text(self.food.x, self.food.y, f"+{pts}", NEON_GREEN)

        self.score += pts
        self.sound.play('eat')

        # Effets particules
        cx = self.food.x * GRID_SIZE + GRID_SIZE // 2
        cy = self.food.y * GRID_SIZE + GRID_SIZE // 2
        self.particles.emit_eat(cx, cy, self.skin['food'])

        # Niveau (tous les 10 points)
        new_level = self.score // 10 + 1
        if new_level > self.level:
            self.level = new_level
            self.sound.play('levelup')
            self.add_floating_text(self.food.x, self.food.y,
                                   f"NIVEAU {self.level}!", NEON_YELLOW)
            # Ajouter un obstacle en boss mode (niveau 5+)
            if self.level >= 5 and len(self.obstacles) < self.level - 3:
                self.obstacles.append(MovingObstacle(GRID_W, GRID_H))

        # Vérifier nouveaux skins débloqués
        newly_unlocked = self.save.check_unlocks(self.score)
        for sk in newly_unlocked:
            self.unlock_notif.append({
                'text': f"SKIN DÉBLOQUÉ: {sk}!",
                'color': SKINS[sk]['glow'],
                'life': 240
            })

        # Spawner nouvelle nourriture
        obs_cells = []
        for obs in self.obstacles:
            obs_cells.extend(obs.get_cells())
        self.food.spawn(self.snake.body, obs_cells)
        self.food.color = self.skin['food']

    def _collect_powerup(self, pu):
        """Gère la collecte d'un power-up."""
        self.powerups.remove(pu)
        self.apply_powerup(pu.type)
        self.sound.play('powerup')
        cx = pu.x * GRID_SIZE + GRID_SIZE // 2
        cy = pu.y * GRID_SIZE + GRID_SIZE // 2
        self.particles.emit_powerup(cx, cy)
        self.add_floating_text(pu.x, pu.y, PowerUp.TYPES[pu.type]['desc'], pu.info['color'])

    def _game_over(self):
        """Termine la partie."""
        self.snake.alive = False
        # Explosion de mort
        head_color = self.skin['head']
        self.particles.emit_death(self.snake.body, head_color)
        self.sound.play('gameover')

    def get_effects_dict(self):
        """Retourne un dict des effets actifs pour le HUD."""
        return {
            'speed':     self.snake.speed_boost,
            'slow':      self.snake.slow_effect,
            'double':    self.snake.double_points,
            'invincible': self.snake.invincible,
        }

    def draw(self, surface):
        """Dessine tout le jeu."""
        # Fond
        surface.fill(DARK_BG)
        draw_grid(surface)

        # Obstacles
        for obs in self.obstacles:
            obs.draw(surface)

        # Nourriture
        self.food.draw(surface)

        # Power-ups
        for pu in self.powerups:
            pu.draw(surface)

        # Serpent
        self.snake.draw(surface, self.skin, self.particles)

        # Particules (par-dessus tout)
        self.particles.draw(surface)

        # Textes flottants
        font = pygame.font.SysFont('Consolas', 16, bold=True)
        for ft in self.floating_texts:
            alpha = int(255 * (ft['life'] / 60))
            txt = font.render(ft['text'], True, ft['color'])
            s = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
            s.blit(txt, (0, 0))
            s.set_alpha(alpha)
            surface.blit(s, (ft['x'] - txt.get_width()//2, int(ft['y'])))

        # Notification skins débloqués
        for i, notif in enumerate(self.unlock_notif):
            alpha = min(255, notif['life'] * 3)
            nf = self.notif_font.render(notif['text'], True, notif['color'])
            ns = pygame.Surface(nf.get_size(), pygame.SRCALPHA)
            ns.blit(nf, (0, 0))
            ns.set_alpha(alpha)
            nx = (GRID_W * GRID_SIZE) // 2 - nf.get_width() // 2
            ny = 30 + i * 30
            surface.blit(ns, (nx, ny))

        # HUD latéral
        self.hud.draw(surface, self.score, self.level, len(self.snake.body),
                      self.combo, self.get_effects_dict(), self.skin_name)

        # Écran de pause
        if self.paused:
            overlay = pygame.Surface((GRID_W * GRID_SIZE, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 130), (0, 0, GRID_W * GRID_SIZE, SCREEN_H))
            surface.blit(overlay, (0, 0))
            draw_glowing_text(surface, "⏸  PAUSE", self.pause_font, NEON_YELLOW,
                              (GRID_W * GRID_SIZE) // 2, SCREEN_H // 2 - 30)
            hint_font = pygame.font.SysFont('Consolas', 18)
            h1 = hint_font.render("P - Reprendre", True, WHITE)
            h2 = hint_font.render("ESC - Menu principal", True, (180, 180, 180))
            cx = (GRID_W * GRID_SIZE) // 2
            surface.blit(h1, h1.get_rect(center=(cx, SCREEN_H//2 + 20)))
            surface.blit(h2, h2.get_rect(center=(cx, SCREEN_H//2 + 48)))

        # Bordure de la zone de jeu
        pygame.draw.rect(surface, NEON_GREEN,
                         (0, 0, GRID_W * GRID_SIZE, SCREEN_H), 2)


# ─── BOUCLE PRINCIPALE ────────────────────────────────────────────────────────
def main():
    """Fonction principale du jeu."""
    # Création de la fenêtre
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("🐍 ULTRA SNAKE - v2.0")
    clock = pygame.time.Clock()

    # Chargement des données
    save_mgr = SaveManager()

    # Écrans
    menu = MenuScreen(save_mgr)
    skin_screen = SkinSelectScreen(save_mgr)
    game_over_screen = GameOverScreen(save_mgr)

    # États de l'application
    STATE_MENU      = 'menu'
    STATE_GAME      = 'game'
    STATE_SKINS     = 'skins'
    STATE_GAMEOVER  = 'gameover'
    state = STATE_MENU

    game_state = None

    # ── BOUCLE PRINCIPALE
    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_mgr.save()
                pygame.quit()
                sys.exit()

            # ── MENU PRINCIPAL
            if state == STATE_MENU:
                action = menu.handle_input(event)
                if action == "JOUER":
                    skin = save_mgr.data.get('selected_skin', 'Classique')
                    game_state = GameState(save_mgr, skin)
                    state = STATE_GAME
                elif action == "SKINS":
                    skin_screen = SkinSelectScreen(save_mgr)
                    state = STATE_SKINS
                elif action == "SCORES":
                    # Affichage highscore déjà dans le menu, on pourrait ajouter un écran dédié
                    pass
                elif action == "QUITTER":
                    save_mgr.save()
                    pygame.quit()
                    sys.exit()

            # ── SÉLECTION DE SKIN
            elif state == STATE_SKINS:
                action = skin_screen.handle_input(event)
                if action in ('select', 'back'):
                    state = STATE_MENU

            # ── EN JEU
            elif state == STATE_GAME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_MENU
                    elif event.key == pygame.K_p:
                        game_state.paused = not game_state.paused
                    # Contrôles du serpent (flèches + ZQSD)
                    elif event.key in (pygame.K_UP, pygame.K_z):
                        game_state.snake.set_direction(0, -1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        game_state.snake.set_direction(0, 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_q):
                        game_state.snake.set_direction(-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        game_state.snake.set_direction(1, 0)

            # ── GAME OVER
            elif state == STATE_GAMEOVER:
                action = game_over_screen.handle_input(event)
                if action == 'restart':
                    skin = save_mgr.data.get('selected_skin', 'Classique')
                    game_state = GameState(save_mgr, skin)
                    state = STATE_GAME
                elif action == 'menu':
                    state = STATE_MENU

        # ── MISE À JOUR
        if state == STATE_MENU:
            menu.update()

        elif state == STATE_GAME and game_state:
            game_state.update()
            # Vérifier si le serpent est mort
            if not game_state.snake.alive:
                # Sauvegarder les données
                new_record = save_mgr.update_highscore(game_state.score)
                save_mgr.data['total_games'] += 1
                newly_unlocked = save_mgr.check_unlocks(game_state.score)
                save_mgr.save()
                # Préparer l'écran game over
                game_over_screen.set_data(
                    game_state.score,
                    game_state.level,
                    len(game_state.snake.body),
                    new_record,
                    newly_unlocked
                )
                state = STATE_GAMEOVER

        # ── RENDU
        if state == STATE_MENU:
            menu.draw(screen)

        elif state == STATE_SKINS:
            skin_screen.draw(screen)

        elif state == STATE_GAME and game_state:
            game_state.draw(screen)

        elif state == STATE_GAMEOVER and game_state:
            # Dessine le jeu en arrière-plan puis l'overlay
            game_state.draw(screen)
            game_over_screen.draw(screen)

        pygame.display.flip()


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
