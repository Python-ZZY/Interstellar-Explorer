try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

import epg
import random
from epg.action import *
from epg.renderer import *

vec = epg.Vector2

APPNAME = "Interstellar Explorer"
WIDTH = 1000
HEIGHT = 600
LV_THRESHOLD = 100
LEVELS = [
("Watery World", "There are only a few weak aliens up there that can be easily defeated.", 1),
("Icy World", "The aliens up there appear to be moving faster because of the extreme weather.", 1.3),
("Mysterious World", "No trace of aliens seems to have been found on this planet.", 1.5),
("Lava World", "The aliens up here are very aggressive.", 1.7),
("The Sun", "Aliens on this planet have no weaknesses and are hard to defeat.", 1.8)
]
MAX_LEVEL = len(LEVELS)

class Particle(epg.sprite.Sprite):
    def __init__(self, x=0, y=0, size=0):
        super().__init__()
        self.life = 10
        self.x = x
        self.y = y
        self.size = size
        self.p_x = random.randint(-5, 5)
        self.p_y = random.randint(-2, 2)

    def particle_player(self, screen):
        for i in range(2):
            epg.draw.circle(screen, (178, 178, 178), (self.x, self.y), self.size)
        self.x += random.randint(-10, 10)
        self.size += 0.5
        self.life -= 0.5
        if self.life <= 0:
            self.kill()

    def particle_enemy(self, screen):
        epg.draw.rect(screen, (255, 0, 0), (self.x, self.y, random.randint(3, 5), random.randint(3, 5)))
        self.x += self.p_x
        self.y += self.p_y
        self.p_y += 0.05
        if self.y > HEIGHT:
            self.kill()

class Player(epg.sprite.Sprite):
    def __init__(self, game):
        super().__init__()

        self.types = {"idle":epg.get_image("player_idle.png"),
        "left":epg.get_image("player_move.png"),"right":epg.image.load_transformed("player_move.png", flip=(True, False))}
        self.image = self.types["idle"]
        self.rect = self.image.get_frect(center=(WIDTH // 2, HEIGHT - 30))

        self.game = game
        self.health = self.healthMax = 100
        self.defense_rate = 0
        self.reset_bar()
        self.update_bar()

        self.vampire = 0
        self.critical_hit = 0

        self.speed = 5
        self.flying_speed = -0.2
        self.original_gravity = 0.5
        self.gravity = 0
        self.vel = vec(0, 0)
        self.particles = epg.sprite.Group()

        self.gun = Gun(self)

    def reset_bar(self):
        self.bar = epg.Surface((self.healthMax + 4, 14))

    def update_bar(self):
        self.bar.fill((0, 0, 0))
        epg.draw.rect(self.bar, (255, 255, 255), (0, 0, self.bar.width, self.bar.height), width=1)
        epg.draw.rect(self.bar, (0, 255, 0), (2, 2, self.health, 10))

    def take_damage(self, damage):
        if random.random() > self.defense_rate:
            if damage:
                self.health -= damage
                epg.play_sound("hit.ogg")
            if self.health > self.healthMax:
                self.health = self.healthMax
            elif self.health <= 0:
                epg.play_sound("lose.ogg")
                self.game.switch(GameOver(self.game))
            self.update_bar()
        else:
            self.game.showtip("Miss", self.rect.center)

    def update(self):
        self.vel.x = 0

        keys = epg.key.get_pressed()
        if keys[epg.K_a]:
            self.vel.x = -self.speed
        elif keys[epg.K_d]:
            self.vel.x = self.speed

        if keys[epg.K_w]:
            self.gravity = self.flying_speed
        else:
            self.gravity = self.original_gravity
        self.vel.y += self.gravity
        self.rect.topleft += self.vel

        if self.vel.x > 0:
            self.image = self.types["right"]
        elif self.vel.x < 0:
            self.image = self.types["left"]
        else:
            self.image = self.types["idle"]

        if self.vel.y < 0:
            self.particles.add(Particle(self.rect.centerx, self.rect.bottom, 10))
        
        if self.rect.bottom >= HEIGHT - 20:
            self.vel.y = self.gravity = 0
            self.rect.bottom = HEIGHT - 20
        elif self.rect.bottom < -50:
            self.take_damage(0.5)

        if self.rect.right < 0:
            self.rect.left = WIDTH
        elif self.rect.left > WIDTH:
            self.rect.right = 0

        self.gun.update()

    def draw(self, screen):
        super().draw(screen)
        for p in self.particles:
            p.particle_player(screen)
        self.gun.draw(screen)

class Bullet(epg.sprite.Sprite):
    id = "bullet"
    speed = 8
    damage = 10

    def __init__(self, game, from_pos, to_pos, is_player=False):
        super().__init__()
        self.game = game
        if not is_player: 
            self.player = game.player
        self.is_player = is_player

        vel = vec(to_pos) - from_pos
        vel.normalize_ip()
        angle = vel.angle_to(vec(1, 0))

        self.image = epg.transform.rotate(epg.get_image(f"{self.id}.png"), angle)
        self.rect = self.image.get_frect(center=from_pos)
        self.vel = vel * self.speed
        self.init()

    def init(self):
        pass

    def fire(self, enemy):
        if self.is_player and random.random() < self.game.player.critical_hit:
            enemy.take_damage(d := self.damage * 2)
            self.game.showtip(d, self.rect.center, color=(255, 0, 0))
        else:
            enemy.take_damage(self.damage)
            self.game.showtip(self.damage, self.rect.center)
        self.kill()

    def update(self):
        self.rect.topleft += self.vel
        if self.rect.bottom < 0 and self.vel.y < 0:
            self.kill()
        elif self.rect.right < 0 or self.rect.left > WIDTH or self.rect.top > HEIGHT:
            self.kill()

        if self.is_player:
            if (enemy := self.game.boss) and self.game.boss != -1:
                if enemy.collide(self.rect):
                    self.fire(enemy)
                    epg.play_sound("hit.ogg")
            for enemy in self.game.enemies:
                if enemy.collide(self.rect):
                    self.fire(enemy)
                    epg.play_sound("hit.ogg")
                    break
        else:
            if self.game.player.rect.colliderect(self.rect):
                self.fire(self.game.player)

class Gun(epg.sprite.Sprite):
    id = "gun"
    bullet_type = Bullet
    fire_rate = 400

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.bullets = player.game.player_bullets

        self.image = self.original_image = epg.get_image(f"{self.id}.png")
        self.last_fire = 0
        self.rate = self.fire_rate
        self.damage = self.bullet_type.damage

    def update(self):
        pos = vec(epg.mouse.get_pos())
        self.offset = pos - self.player.rect.center
        self.offset.normalize_ip()
        self.angle = self.offset.angle_to(vec(1, 0))

        if self.offset.x > 0:
            self.image = epg.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(midleft=self.player.rect.midright)
            from_pos = self.rect.midright
        else:
            self.image = epg.transform.rotate(epg.transform.flip(self.original_image, False, True), self.angle)
            self.rect = self.image.get_rect(midright=self.player.rect.midleft)
            from_pos = self.rect.midleft

        now = epg.get_time()
        if now - self.last_fire >= self.rate:
            self.last_fire = now
            b = self.bullet_type(self.player.game, from_pos, pos, is_player=True)
            b.damage = self.damage
            self.bullets.add(b)

class Enemy(epg.AStatic):
    health = 0
    speed = 0
    fire_rate = 3000

    def __init__(self, game, pos=None):
        self.game = game
        self.player = game.player
        self.health = self.healthMax = self.__class__.health
        if pos:
            super().__init__(self.get_surface(), center=pos, use_float=True)
        else:
            super().__init__(self.get_surface(), centerx=random.randint(0, WIDTH), bottom=-1, use_float=True)
        self.last_fire = 0
        self.wait_to = 0
        self.init()

    def shoot(self, bullet_type, from_pos=None, to_pos=None):
        return self.game.shoot(bullet_type, from_pos if from_pos else self.rect.center, to_pos)

    def wait(self, time):
        self.wait_to = epg.get_time() + self.wait_to

    def init(self):
        pass

    def get_surface(self):
        pass

    def fire(self):
        pass

    def collide(self, rect):
        return self.rect.colliderect(rect)

    def move(self):
        vel = (vec(self.player.rect.center) - self.rect.center).normalize() * self.speed
        self.rect.topleft += vel

    def update(self):
        now = epg.get_time()

        if now >= self.wait_to:
            self.move()

        if now - self.last_fire >= self.fire_rate:
            self.last_fire = now
            self.fire()

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.die()
            self.kill()

            self.game.death += 1
            epg.play_sound("death.ogg")

            if self.player.vampire:
                v = int(self.player.healthMax * self.player.vampire)
                self.player.take_damage(-v)
                self.game.showtip(v, self.player.rect.center, color=(0, 255, 0))

            if not (self.game.boss or self.game.win):
                if self.game.death > self.game.max_death:
                    self.game.add_boss()

    def die(self):
        for i in range(20):
            self.game.enemy_particles.add(Particle(self.rect.centerx, self.rect.centery))

class Boss(Enemy):
    health = 0
    speed = 0

    def init(self):
        self.bar = epg.Surface((WIDTH - 50, 14))
        self.take_damage(0)

    def take_damage(self, damage):
        self.health -= damage
        self.bar.fill((0, 0, 0))
        epg.draw.rect(self.bar, (255, 255, 255), (0, 0, self.bar.width, self.bar.height), width=1)
        epg.draw.rect(self.bar, (255, 0, 0), (2, 2, self.health / self.healthMax * self.bar.width, 10))
        if self.health <= 0:
            self.die()
            for enemy in self.game.enemies:
                enemy.take_damage(enemy.healthMax)
            self.game.boss = None
            self.game.end_game()

class Enemy1(Enemy):
    health = 20
    speed = 2

    def get_surface(self):
        return epg.get_image("enemy1.png")

    def fire(self):
        self.shoot(EnemyBullet1)

    def draw(self, screen, color=(255, 0, 0)):
        screen.blit(self.image, self.rect)
        offset = (vec(self.player.rect.center) - self.rect.center).normalize() * 4
        epg.draw.circle(screen, color, self.rect.center + offset, 8)

class EnemyBullet1(Bullet):
    id = "enemy_bullet1"
    damage = 10
    speed = 4

class Boss1(Boss):
    health = 500
    speed = 1.5
    fire_rate = 3000

    def init(self):
        super().init()
        self.fire_count = 0

    def get_surface(self):
        return epg.get_image("boss1.png")

    def die(self):
        for i in range(n := 36):
            to_pos = vec(1, 0)
            to_pos.rotate_ip(360 / n * i)
            b = self.game.shoot(EnemyBullet1, self.rect.center, self.rect.center + to_pos)
            b.vel *= 2

    def fire(self):
        self.shoot(BossBullet1)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        offset = (vec(self.player.rect.center) - self.rect.center).normalize() * 12
        epg.draw.circle(screen, (60, 60, 60), self.rect.center + offset, 29)

class BossBullet1(Bullet):
    id = "boss_bullet1"
    damage = 20
    speed = 4.2

    def init(self):
        self.life = 100

    def update(self):
        self.vel = (vec(self.player.rect.center) - self.rect.center).normalize() * self.speed
        super().update()

        self.life -= 0.5
        if self.life <= 0:
            self.kill()
            b = self.game.shoot(EnemyBullet1, self.rect.center)
            b.vel *= 2

class Boss2(Boss):
    health = 600
    speed = 2.5
    fire_rate = 1600

    def init(self):
        super().init()
        self.rect.midtop = (WIDTH // 2, 2)
        self.eye_x = 0
        self.direction = 1
        self.eye_image = epg.get_image("boss2eye.png")

    def get_surface(self):
        return epg.get_image("boss2.png")

    def move(self):
        self.rect.x += self.direction * self.speed
        if self.rect.right >= WIDTH or self.rect.left <= 0:
            self.direction = -self.direction

    def fire(self):
        self.game.add_enemy(Enemy2, self.rect.center)

    def draw(self, screen):
        if self.rect.centerx > self.player.rect.centerx:
            self.eye_x = -15
        elif self.rect.centerx < self.player.rect.centerx:
            self.eye_x = 15
        else:
            self.eye_x = 0

        screen.blit(self.image, self.rect)
        screen.blit(self.eye_image, self.rect.center + vec(self.eye_x - 30, -30))

class Enemy2(Enemy1):
    def init(self):
        self.speed = random.uniform(1.8, 3.5)

    def get_surface(self):
        return epg.get_image("enemy2.png")

    def fire(self):
        self.shoot(EnemyBullet2)

    def draw(self, screen):
        super().draw(screen, (180, 230, 219))

class EnemyBullet2(EnemyBullet1):
    id = "enemy_bullet2"
    speed = 4.2

class Boss3(Boss):
    health = 550
    speed = 1.2
    fire_rate = 5000

    def init(self):
        super().init()
        self.fire_counter = 0
        self.visible = True
        self.change_delta = 2500
        self.last_change = epg.get_time() + self.change_delta

    def collide(self, rect):
        if self.visible:
            return super().collide(rect)

    def get_surface(self):
        return epg.get_image("boss3.png")

    def fire(self):
        self.fire_counter = 1

    def update(self):
        super().update()

        if self.fire_counter:
            if self.fire_counter % 10 == 0:
                b = self.shoot(EnemyBullet3)
                if not self.visible:
                    b.image.set_alpha(10)
            self.fire_counter += 1
            if self.fire_counter > 100:
                self.fire_counter = 0

        now = epg.get_time()
        if now - self.last_change >= self.change_delta:
            self.last_change = now
            self.visible = not self.visible
            if self.visible:
                self.image.set_alpha(255)
            else:
                self.image.set_alpha(10)

    def draw(self, screen):
        self.eye_image = epg.get_image("boss3eye.png")
        if self.rect.centerx > self.player.rect.centerx:
            self.eye_image = epg.transform.flip(self.eye_image, True, False)
        if self.rect.centery > self.player.rect.centery:
            self.eye_image = epg.transform.flip(self.eye_image, False, True)
        if self.visible:
            self.eye_image.set_alpha(255)
        else:
            self.eye_image.set_alpha(10)

        screen.blit(self.image, self.rect)
        screen.blit(self.eye_image, self.rect)

class EnemyBullet3(EnemyBullet1):
    id = "boss_bullet1"

class Enemy3(Enemy1):
    health = 25
    speed = 2

    def get_surface(self):
        return epg.get_image("enemy3.png")

    def fire(self):
        b = self.shoot(EnemyBullet3)
        b.image.set_alpha(30)

    def draw(self, screen):
        super().draw(screen, (0, 0, 0, 200))

class Boss4(Boss):
    health = 550
    speed = 1.5
    fire_rate = 1000

    def init(self):
        super().init()
        self.angle = 0
        self.rush_counter = 0

    def get_surface(self):
        return epg.get_image("boss4.png")

    def fire(self):
        self.shoot(EnemyBullet4)

    def draw(self, screen):
        self.eye_image = epg.get_image("boss4eye.png")
        if self.rect.centerx > self.player.rect.centerx:
            self.eye_image = epg.transform.flip(self.eye_image, True, False)
        if self.rect.centery > self.player.rect.centery:
            self.eye_image = epg.transform.flip(self.eye_image, False, True)

        screen.blit(self.image, self.rect)
        screen.blit(self.eye_image, self.eye_image.get_rect(center=self.rect.center))

    def update(self):
        super().update()

        self.angle += 6
        if self.angle == 360:
            self.angle = 0
        self.image = epg.transform.rotate(epg.get_image("boss4.png"), self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        if self.rect.colliderect(self.player.rect):
            self.player.take_damage(1)

        self.rush_counter += 1
        if 150 < self.rush_counter % 250 < 250:
            self.speed = 15
        else:
            self.speed = 1.5

class EnemyBullet4(Bullet):
    id = "enemy_bullet4"

    def init(self):
        self.angle = 0

    def fire(self, enemy):
        enemy.take_damage(1)

    def update(self):
        super().update()

        self.angle += 12
        if self.angle == 360:
            self.angle = 0
        self.image = epg.transform.rotate(epg.get_image("enemy_bullet4.png"), self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Enemy4(Enemy1):
    speed = 1.5
    fire_rate = 2000

    def get_surface(self):
        return epg.get_image("enemy4.png")

    def fire(self):
        self.shoot(EnemyBullet4)

class Boss5(Boss):
    health = 600
    speed = 1
    fire_rate = 80

    def init(self):
        super().init()
        self.fire_counter = 0

    def fire(self):
        v = self.fire_counter % 100
        if 40 < v < 50:
            for i in range(n := 18):
                to_pos = vec(1, 0)
                to_pos.rotate_ip(360 / n * i + self.fire_counter * 7)
                b = self.game.shoot(EnemyBullet5, self.rect.center, self.rect.center + to_pos)
                b.vel *= 2
        elif 95 < v < 100:
            self.game.add_enemy(Enemy5, self.rect.center)
        self.fire_counter += 1

    def get_surface(self):
        return epg.get_image("boss5.png")

    def draw(self, screen):
        self.eye_image = epg.get_image("boss5eye.png")
        if self.rect.centerx > self.player.rect.centerx:
            self.eye_image = epg.transform.flip(self.eye_image, True, False)
        if self.rect.centery > self.player.rect.centery:
            self.eye_image = epg.transform.flip(self.eye_image, False, True)

        screen.blit(self.image, self.rect)
        screen.blit(self.eye_image, self.eye_image.get_rect(center=self.rect.center))

class Enemy5(Enemy1):
    health = 22
    fire_rate = 1500

    def init(self):
        self.speed = random.uniform(3, 4)

    def get_surface(self):
        return epg.get_image("enemy5.png")

    def fire(self):
        self.shoot(EnemyBullet5)

    def draw(self, screen):
        super().draw(screen, (255, 255, 0))

class EnemyBullet5(EnemyBullet1):
    id = "enemy_bullet1"
    speed = 7

class Star(epg.AStatic):
    def __init__(self):
        size = random.randint(1, 4)
        surf = epg.Surface((size, size))
        surf.fill((255, 255, 255))
        super().__init__(surf, center=(random.randint(10, WIDTH - 10), random.randint(10, HEIGHT // 2)))
        self.act(
            (FadeIn(random.randint(1000,10000)) >> Delay(random.randint(1000,10000)) >> \
                FadeOut(random.randint(1000,10000))) * float("inf")
            )

class BG(epg.AScene):
    def init(self):
        self.effects = epg.sprite.Group()
        self.fade_colors = [(0, 0, 64), (10, 10, 10), (64, 0, 64)]
        self.fade_incr = 0.0005
        self.fade_pos = 0
        self.stars = epg.sprite.Group()
        for i in range(random.randint(10, 24)):
            self.stars.add(Star())

    def play_smoke_effect(self):
        if not self.effects:
            n = 100
            dx, dy = WIDTH / n, HEIGHT / n
            for x in range(n):
                for y in range(n):
                    self.effects.add(Particle(x=x * dx, y=y * dy))

    def draw_effects(self):
        for eff in self.effects:
            eff.particle_player(self.screen)

    def draw(self):
        self.screen.fill(epg.math.mix(self.fade_colors[0], self.fade_colors[1], self.fade_pos))
        self.stars.draw(self.screen)
        
    def update(self):
        self.stars.update()
        self.fade_pos += self.fade_incr
        if self.fade_pos > 1:
            self.fade_pos = 0
            c = self.fade_colors[0]
            self.fade_colors.pop(0)
            self.fade_colors.append(c)

class AbilityManager:
    def __init__(self, abilities):
        self.current_abilities = abilities
        inf = float("inf")
        self.abilities = {
        "speed up":("Speed + 30%", 2),
        "get stronger":("Attack + 40%", inf),
        "strong defense":("15% chance of immune damage", 1),
        "energy boost":("Health Upper Limit + 25%", 4),
        "rush attack":("Attack Cooldown - 30%", 3),
        "vampire":("Restore 2% health after killing a common alien", 1),
        "critical hit":("20% chance of doubling damage", 1),
        }

    def update(self, player):
        self.player = player
        for ability, count in self.current_abilities.items():
            for i in range(count):
                getattr(self, ability.replace(" ", "_"))()

    def add(self, ability):
        self.current_abilities.setdefault(ability, 0)
        self.current_abilities[ability] += 1

    def get_selectable_abilities(self, n=3):
        abts = self.abilities.copy()
        for ability in self.abilities:
            if self.current_abilities.get(ability, 0) >= self.abilities[ability][1]:
                del abts[ability]
        return random.sample(tuple(abts.items()), n)

    def speed_up(self):
        self.player.speed = round(self.player.speed * 1.3, 1)

    def get_stronger(self):
        self.player.gun.damage = int(self.player.gun.damage * 1.4)

    def strong_defense(self):
        self.player.defense_rate = 0.15

    def energy_boost(self):
        d = int(self.player.healthMax * 0.25)
        self.player.healthMax += d
        self.player.health += d
        self.player.reset_bar()
        self.player.update_bar()

    def rush_attack(self):
        self.player.gun.rate = int(self.player.gun.rate * 0.7)

    def vampire(self):
        self.player.vampire = 0.02

    def critical_hit(self):
        self.player.critical_hit = 0.2

class TextButton(epg.Static):
    def __init__(self, text, color=(255, 255, 255), activecolor=(0, 0, 255), command=None, **kw):
        self.text = text
        self.kw = kw
        self.color = self.defaultcolor = color
        self.activecolor = activecolor
        self.command = command
        super().__init__(epg.text_render(text, color=self.color, **kw))

    def events(self, event):
        if event.type == epg.MOUSEBUTTONUP and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.command:
                    epg.play_sound("click.ogg")
                    self.command()

    def update(self):
        pos = epg.mouse.get_pos()
        if self.rect.collidepoint(pos):
            color = self.activecolor
        else:
            color = self.defaultcolor

        if self.color != color:
            self.color = color
            self.image = epg.text_render(self.text, color=self.color, **self.kw)

class GameOver(epg.AScene):
    def __init__(self, game):
        self.game = game
        self.game.main_menu.total_time += epg.get_time() - self.game.start_time
        super().__init__()

    def init(self):
        self.text = epg.AStatic(epg.text_render("Game Over", color=(255, 0, 0), size=30), center=(WIDTH//2, HEIGHT//2))
        self.text.act(ScaleBy(1000, range=(0, 1)) >> Shake(100, dist=(3,3)) * 5)

    def events(self, event):
        if event.type in (epg.MOUSEBUTTONDOWN, epg.KEYDOWN):
            self.act(FadeOut(1000) >> Switch(scene=LevelChooser(self.game.main_menu)))

    def update(self):
        self.text.update()

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.text.draw(self.screen)

class Win(BG):
    def __init__(self, game):
        self.game = game
        self.game.main_menu.level += 1
        self.game.main_menu.total_time += epg.get_time() - self.game.start_time
        super().__init__()

    def init(self):
        super().init()
        if self.game.main_menu.level > MAX_LEVEL:
            self.switch(Congratulations(self.game.main_menu))
            return

        self.act(FadeIn(1000))

        self.buttons = epg.sprite.Group()
        g = self.group_all = epg.sprite.Group()
        g.add(epg.Static(
            epg.text_render(f"You beat the boss of {LEVELS[self.game.level-1][0]}!\nSelect your ability:", 
                color=(255, 255, 0)), center=(WIDTH / 2, HEIGHT / 5 - 50)))

        abts = self.game.abilities.get_selectable_abilities()
        orig_surf = epg.Surface((WIDTH // 3.5, HEIGHT // 2.5)).convert_alpha()
        orig_surf.fill((200, 200, 0, 200))
        d = (WIDTH - len(abts) * orig_surf.width) / (len(abts) + 1)
        for i, (a, (doc, _)) in enumerate(abts):
            surf = orig_surf.copy()
            s = epg.AStatic(surf, midleft=(d + i * (surf.width + d), HEIGHT / 2))
            s.id = a
            s.act(ScaleBy(400, range=((0, 1), (1, 1))))
            self.buttons.add(s)
            r = epg.text_render(a.title(), size=26, color=(255, 255, 255))
            surf.blit(r, r.get_rect(center=(surf.width / 2, surf.height / 3)))
            r = epg.text_render(doc, size=20, color=(255, 255, 255), wraplength=surf.width - 10)
            surf.blit(r, r.get_rect(center=(surf.width / 2, surf.height / 3 * 2)))

    def events(self, event):
        if event.type == epg.MOUSEBUTTONUP and event.button == 1:
            for s in self.buttons:
                if s.rect.collidepoint(event.pos):
                    epg.play_sound("click.ogg")
                    self.game.abilities.add(s.id)
                    epg.data.dump([self.game.main_menu.level, self.game.abilities.current_abilities, self.game.main_menu.total_time])
                    for b in self.buttons:
                        b.kill()
                    self.group_all.add(s)
                    def f(s):
                        self.act(FadeOut(400) >> Switch(scene=LevelChooser(self.game.main_menu)))
                    s.act(ScaleBy(1000, range=(1, 1.3)) + \
                        MoveTo(1000, range=(WIDTH//2, HEIGHT//2), anchor="center") >> f)

    def update(self):
        super().update()
        self.group_all.update()
        self.buttons.update()

    def draw(self):
        super().draw()
        self.group_all.draw(self.screen)
        self.buttons.draw(self.screen)

        pos = epg.mouse.get_pos()
        for s in self.buttons:
            if s.rect.collidepoint(pos):
                epg.draw.rect(self.screen, (255, 255, 0), s.rect, width=2)

class Story(BG):
    story = [
"In 2100 AD, Earth's resources were almost exhausted.",
"As a result, humanity decided to explore five selected planets in outer space.",
"You've been chosen to lead the space exploration team.",
"However, these planets are full of dangerous aliens. They take no pity on the invaders at all.",
"@You represent the glory of humanity!\nGood luck to you!"]
    font = (24, WIDTH // 2)

    def __init__(self, main_menu):
        self.main_menu = main_menu
        super().__init__()

    def init(self):
        super().init()
        self.group_all = epg.sprite.Group()
        self.index = -1
        self.next()

    def end_command(self, s=None):
        self.switch(LevelChooser(self.main_menu))

    def next(self, s=None):
        self.index += 1
        if self.index >= len(self.story):
            self.play_smoke_effect()
            self.act(Delay(300) >> FadeOut(300) >> self.end_command)
        else:
            for s in self.group_all:
                s.kill()

            t = self.story[self.index]
            c = (255, 255, 0) if t.startswith("@") else (255, 255, 255)
            s = epg.AStatic(epg.text_render(self.story[self.index].replace("@", ""), 
                size=self.font[0], color=c, wraplength=self.font[1]), 
                center=(WIDTH / 2, HEIGHT / 2))
            s.act(FadeIn(2000) >> Delay(1000) >> FadeOut(2000) >> self.next)
            self.group_all.add(s)

    def events(self, event):
        if event.type == epg.MOUSEBUTTONUP and event.button == 1:
            epg.play_sound("click.ogg")
            self.next()

    def update(self):
        super().update()
        self.group_all.update()

    def draw(self):
        super().draw()
        self.group_all.draw(self.screen)
        self.draw_effects()

class ControlsPage(Story):
    story = [
    "@Press <A> to move left, <D> to move right.",
    "@Hold <W> to fly.",
    "@The bar at the top left of the screen shows the player's health.",
    "@Don't forget that the left side of the screen is connected to the right side. \nWhen you exit from the left side, you will return to the right side.",
    "@Have a good time!"
    ]
    def end_command(self, s=None):
        self.switch(MainMenu())

class Congratulations(Story):
    font = (28, 0)

    def init(self):
        t = self.main_menu.total_time // 1000
        min = int(t / 60)
        s = int(t - min * 60)
        self.story = ["@Congratulations!\n\nYou Win!", "total playtime: {}min {}s".format(min, s)]
        super().init()

    def end_command(self, s=None):
        self.switch(CreditsPage())

class CreditsPage(BG):
    def init(self):
        if not epg.mixer.music.get_busy():
            epg.mixer.music.play(-1)

        super().init()

        self.credits = [
        (APPNAME, 40, "gold"),
        "",
        ("Created by", 22, "white"),
        ("Python-ZZY", 36, "gold"),
        "",
        ("itch:", 22, "white"),
        ("https://python-zzy.itch.io/", 26, "white"),
        "",
        ("github:", 22, "white"),
        ("https://github.com/Python-ZZY", 26, "white"),
        "",
        ("some resources are made with these generators below:", 22, "white"),
        ] + [(t, 26, "white") for t in (
            "Pixel Planet Generator by deep-fold.itch.io",
            "jsfxr (sound)",
            "TuneFlow (music)",
            "Layer AI (icon)"
            )] + \
        ["",
        ("Made for Pygame Community Summer Jam 2024", 26, "orange"),
        ("Made with pygame-ce 2.5.0", 26, "orange"),
        "",
        ("Thanks for playing!", 30, "gold"),
        "","", ""
        ]
        
        self.act(FadeIn(500))

        self.add_group("all")
        self.id = 0
        self.next()

    def onexit(self):
        self.switch(MainMenu())
        
    def update(self):
        self.group_all.update()
        super().update()

    def draw(self):
        super().draw()
        self.group_all.draw(self.screen)

    def next(self, *a):
        if self.id == len(self.credits):
            self.id = 0
        
        c = self.credits[self.id]
        a = Delay()
        if c == "" or c[0] == "":
            a = Delay(1600) >> Call(func=self.next) >> Kill()
            text, size, color = "", 1, "white"
        else:
            if isinstance(c, str):
                text, size, color = c.rstrip("\n"), 22, "white"
            else:
                text, size, color = c[0], c[1], c[2]
                try:
                    a = c[3]
                except IndexError:
                    pass

            base = FadeOut() + Rotate(range=(0, 180)) >> Delay(600) >> FadeIn(1000) + \
            Rotate(1000, range=(0, 180), cover=False)
            a = base >> Call(func=self.next) >> MoveBy(8000, range=(0, -self.height * .75 + 30)) + a >> \
            ScaleBy(800, range=((1, 1), (0, 1))) >> Kill()
        sprite = epg.AStatic(epg.text_render(text, size, color,
            wraplength=int(WIDTH * 0.8)), a, center=(self.centerx, self.height * .75))
        self.group_all.add(sprite)

        self.id += 1

class MainMenu(BG):
    def init(self):
        super().init()
        self.act(FadeIn(1000))
        try:
            self.level, abilities, self.total_time = epg.data.load(error=True)
            self.play_story = False
        except FileNotFoundError:
            self.level, abilities, self.total_time = 1, {}, 0
            self.play_story = True
        self.abilities = AbilityManager(abilities)
        self.add_group("all")

        s = epg.AStatic(epg.load_image("logo.png"), center=(WIDTH / 2, 140))
        self.group_all.add(s)
        s.act(FadeIn(500) >> (FadeOut(500) >> FadeIn(500)) * 2)

        self.y = 320
        self.button("Start", self.start_game)
        self.button("Controls", self.controls)
        self.button("Credits", lambda: self.switch(CreditsPage()))
        self.button("Exit", self.onexit)

    def button(self, text, command):
        b = TextButton(text, size=26, command=command)
        b.rect.center = (WIDTH / 2, self.y)
        self.y += 50
        self.group_all.add(b)

    def start_game(self):
        epg.mixer.music.play(-1)
        self.play_smoke_effect()
        self.act(Delay(300)>>FadeOut(300)>>Switch(scene=Story(self) if self.play_story else LevelChooser(self, False)))

    def controls(self):
        self.switch(ControlsPage(self))

    def events(self, event):
        for g in self.group_all:
            if hasattr(g, "events"):
                g.events(event)

    def update(self):
        super().update()
        self.group_all.update()

    def draw(self):
        super().draw()
        self.group_all.draw(self.screen)
        self.draw_effects()

class Planet(epg.ADynamic):
    def __init__(self, level, scale, **kw):
        self.level = level
        im = epg.transform.scale_by(epg.load_image(f"level{level}.png"), scale)
        super().__init__({"":epg.Animation(im, x=25, y=10, interval=50)}, **kw)

class LevelChooser(BG):
    def __init__(self, main_menu, play_effect=True):
        self.main_menu = main_menu
        self.level, self.abilities = main_menu.level, main_menu.abilities
        self.play_effect = play_effect
        super().__init__()

    def init(self):
        super().init()
        lv = LEVELS[self.level-1]
        g = self.group_all = epg.sprite.Group()
        g.add(p := Planet(self.level, lv[2], center=(WIDTH / 2, HEIGHT / 2)))

        r = renders(Text(f"No.{self.level} {lv[0]}", size=22, color=(255, 255, 0)), Text(lv[1]))
        g.add(r := epg.AStatic(r, center=(WIDTH / 2, 110)))

        b = self.button = TextButton("Explore!", size=26, command=self.explore)
        b.rect.center = (WIDTH / 2, HEIGHT - 110)
        g.add(b)

        if self.play_effect:
            p.act(FadeIn(5000) >> Clear())
            r.act(FadeIn(500) >> (FadeOut(500) >> FadeIn(500)) * 2 >> Clear())

    def explore(self):
        self.play_smoke_effect()
        self.act(Delay(300) >> FadeOut(300) >> Switch(scene=Game(self.main_menu, self.level, self.abilities)))

    def events(self, event):
        self.button.events(event)

    def update(self):
        super().update()
        self.group_all.update()

    def draw(self):
        super().draw()
        self.group_all.draw(self.screen)
        self.draw_effects()

class Game(BG):
    TIP_ACTION = FadeIn(100) >> MoveBy(500, range=(0, -10)) + FadeOut(500) >> Kill()

    def __init__(self, main_menu, level, abilities):
        self.main_menu = main_menu
        self.level = level
        self.abilities = abilities
        self.max_death = 10 + level * 5
        self.win = False
        super().__init__()

    def init(self):
        super().init()
        self.player_bullets = epg.sprite.Group()
        self.enemy_bullets = epg.sprite.Group()
        self.player = Player(self)
        self.abilities.update(self.player)
        self.enemies = epg.sprite.Group()
        self.enemy_particles = epg.sprite.Group()
        self.tips = epg.sprite.Group()
        self.boss = None
        self.start_time = epg.get_time()

        self.add_enemy_rate = 4300 * 0.8 ** self.level
        self.last_add_enemy = epg.get_time()
        self.death = 0

        self.bg = epg.load_image("bg{}.png".format(self.level))
        self.bg_pos = self.bg.get_rect(bottomleft=(0, HEIGHT)).topleft

        if self.level != 3:
            self.showtext("Aliens descend in droves!")

    def shoot(self, bullet_type, from_pos, to_pos=None):
        b = bullet_type(self, from_pos, to_pos if to_pos else self.player.rect.center)
        self.enemy_bullets.add(b)
        return b

    def add_enemy(self, enemy_type, pos=None):
        self.enemies.add(e := enemy_type(self, pos=pos))
        return e

    def showtip(self, tip, pos, **kw):
        tip = epg.AStatic(epg.text_render(str(tip), **kw), center=pos)
        tip.act(self.TIP_ACTION)
        self.tips.add(tip)

    def showtext(self, tip, color="red", func=None, blink=True):
        if not func: 
            func = lambda s: None
        y = 140
        s = epg.AStatic(epg.get_image(f"line_{color}.png"), x=0, centery=y)
        s.act( MoveBy(2500, range=((0, 0), (-1000, 0))) >> FadeOut(500)>> func >> Kill() )
        self.tips.add(s)
        s = epg.AStatic(epg.get_image(f"line_{color}.png"), right=WIDTH, centery=HEIGHT - y)
        s.act( MoveBy(2500, range=((0, 0), (1000, 0))) >> FadeOut(500) >> Kill() )
        self.tips.add(s)
        r = epg.text_render(tip, color=color, size=50)
        s = epg.AStatic(r, center=(WIDTH / 2, HEIGHT / 2))
        if blink:
            s.act((FadeIn(500) >> FadeOut(500)) * 3 >> Kill())
        else:
            s.act(FadeIn(500))
        self.tips.add(s)

    def end_game(self):
        self.win = True
        def f(s):
            self.play_smoke_effect()
            self.act(FadeOut(1000) >> Switch(scene=Win(self)))
        self.showtext("Victory!", color="yellow", func=f, blink=False)

    def add_boss(self):
        self.boss = -1
        def f(s):
            self.boss = eval("Boss{}".format(self.level))(self)
        self.showtext("The Boss is coming!", func=f)
        epg.play_sound("warning.ogg")

    def update(self):
        super().update()
        self.player.update()
        self.enemies.update()
        if self.boss and self.boss != -1: self.boss.update()
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.enemy_particles.update()
        self.tips.update()

        now = epg.get_time()
        if now - self.last_add_enemy >= self.add_enemy_rate and not self.boss and not self.win:
            self.last_add_enemy = now
            enemy_type = eval("Enemy{}".format(self.level))
            self.add_enemy(enemy_type)
            if random.random() < self.level / 10 + 0.1:
                self.add_enemy(enemy_type)

    def draw(self):
        super().draw()
        self.screen.blit(self.bg, self.bg_pos)
        self.enemy_bullets.draw(self.screen)
        self.player_bullets.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        if self.boss and self.boss != -1: self.boss.draw(self.screen)
        self.player.draw(self.screen)
        for p in self.enemy_particles:
            p.particle_enemy(self.screen)

        self.screen.blit(self.player.bar, (28, 48))
        if self.boss and self.boss != -1:
            self.screen.blit(self.boss.bar, (28, 28))
        self.tips.draw(self.screen)
        self.draw_effects()

if __name__ == '__main__':
    epg.assets = "assets"
    epg.font.set_default("font.ttf")
    app = epg.init((WIDTH, HEIGHT), caption=APPNAME, icon=epg.load_image("icon.ico"), flags=epg.SCALED)
    epg.mixer.music.load(epg.get_asset("bgm.mp3"))
    epg.mixer.music.set_volume(0.4)
    app.run(MainMenu())
