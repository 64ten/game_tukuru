import pygame
import sys
import random
import math

pygame.init()

# =====================================
# 設定・定数
# =====================================
WIDTH = 1280
HEIGHT = 750
UI_HEIGHT = 25
XP_BAR_HEIGHT = 30

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
MAGENTA = (255, 0, 255)
GREEN = (0, 255, 0)
DARK_GRAY = (50, 50, 50)

skills = [
    "fire_rate_up",
    "pierce_bullet",
    "speed_up",
    "barrier",
    "atk_up",
    "hp_up",
    "heal",
    "exp_range_up",
    "pierce_knockback"
]

skill_names = {
    "fire_rate_up": "連射速度アップ",
    "pierce_bullet": "貫通弾（5秒毎射撃）",
    "speed_up": "移動速度アップ",
    "barrier": "一度きりのバリア（重複不可）",
    "atk_up": "攻撃力アップ (+50%)",
    "hp_up": "最大HP増加 (+2)",
    "heal": "HPを大幅回復 (60%)",
    "exp_range_up": "経験値収集範囲アップ",
    "pierce_knockback": "貫通弾ノックバック強化"
}

# =====================================
# ウェーブ設定 (出現上限, 出現間隔, 敵の出現重み)
# =====================================
WAVE_CONFIG = {
    1: {"max_enemies": 8,  "spawn_interval": 1500, "weights": {"Enemy": 1.0}},
    2: {"max_enemies": 10, "spawn_interval": 1400, "weights": {"Enemy": 1.0}},
    3: {"max_enemies": 12, "spawn_interval": 1300, "weights": {"Enemy": 1.0}},
    4: {"max_enemies": 15, "spawn_interval": 1200, "weights": {"Enemy": 0.7, "HeavyEnemy": 0.3}},
    5: {"max_enemies": 8,  "spawn_interval": 1500, "weights": {"Enemy": 0.7, "HeavyEnemy": 0.3}},
    6: {"max_enemies": 20, "spawn_interval": 1000, "weights": {"Enemy": 0.4, "HeavyEnemy": 0.3, "ShootingEnemy": 0.3}},
    7: {"max_enemies": 25, "spawn_interval": 800,  "weights": {"Enemy": 0.3, "HeavyEnemy": 0.4, "ShootingEnemy": 0.3}},
    # 以降はDEFAULT_WAVE_SETTINGを適用
}
DEFAULT_WAVE_SETTING = {"max_enemies": 30, "spawn_interval": 600, "weights": {"Enemy": 0.2, "HeavyEnemy": 0.4, "ShootingEnemy": 0.4}}



# スクリーン・フォント設定
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Shooting Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("msgothic", 64)
small_font = pygame.font.SysFont("msgothic", 20)

# =====================================
# クラス定義
# =====================================

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.speed = 4
        self.shoot_cooldown = 1000
        self.last_shot_time = 0
        self.hp = 5
        self.max_hp = 5
        self.invincible_timer = 0 # 被弾後の無敵時間
        self.has_barrier = False
        self.atk_multiplier = 1.0
        self.pickup_range = 100

    def update(self, keys):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < HEIGHT - XP_BAR_HEIGHT:
            self.rect.y += self.speed

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (4, 4), 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.speed = 8

    def update(self):
        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed
        # 画面外に出たら消去
        if (self.rect.x < -100 or self.rect.x > WIDTH + 100 or 
            self.rect.y < -100 or self.rect.y > HEIGHT + 100):
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (4, 4), 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.speed = 5

    def update(self):
        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed
        if not screen.get_rect().inflate(200, 200).contains(self.rect):
            self.kill()

class PiercingBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (6, 6), 6)
        pygame.draw.circle(self.image, WHITE, (6, 6), 3) # 中心を白くして強調
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.speed = 12
        self.hit_enemies = set() # すでに当たった敵を記録

    def update(self):
        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed
        if not screen.get_rect().inflate(200, 200).contains(self.rect):
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(RED)
        self.hp = 1
        self.max_hp = 1
        
        side = random.randint(0, 3)
        if side == 0: # Top
            x, y = random.randint(0, WIDTH), -self.size
        elif side == 1: # Bottom
            x, y = random.randint(0, WIDTH), HEIGHT + self.size
        elif side == 2: # Left
            x, y = -self.size, random.randint(0, HEIGHT)
        else: # Right
            x, y = WIDTH + self.size, random.randint(0, HEIGHT)
            
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 1.5

    def update(self, player_pos):
        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

class HeavyEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.size = 40 # 赤色のザコより少し大きく
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(ORANGE)
        
        side = random.randint(0, 3)
        if side == 0: # Top
            x, y = random.randint(0, WIDTH), -self.size
        elif side == 1: # Bottom
            x, y = random.randint(0, WIDTH), HEIGHT + self.size
        elif side == 2: # Left
            x, y = -self.size, random.randint(0, HEIGHT)
        else: # Right
            x, y = WIDTH + self.size, random.randint(0, HEIGHT)
            
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hp = 3 # 赤色のザコの3倍
        self.max_hp = 3
        self.speed = 1.2 # 赤色より若干遅く

class ShootingEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.image.fill(YELLOW)
        self.shoot_cooldown = 2000
        self.last_shot_time = pygame.time.get_ticks() + random.randint(0, 1000)

    def shoot(self, player_pos, enemy_bullets, all_sprites):
        # 画面外にいるときは射撃しない
        if not screen.get_rect().collidepoint(self.rect.center):
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.shoot_cooldown:
            dx = player_pos[0] - self.rect.centerx
            dy = player_pos[1] - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist != 0:
                bullet = EnemyBullet(self.rect.centerx, self.rect.centery, dx/dist, dy/dist)
                enemy_bullets.add(bullet)
                all_sprites.add(bullet)
            self.last_shot_time = current_time

class MidBoss(ShootingEnemy):
    def __init__(self):
        super().__init__()
        self.size = 80
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(YELLOW)
        pygame.draw.rect(self.image, WHITE, self.image.get_rect(), 4)
        self.rect = self.image.get_rect(center=(WIDTH//2, -self.size))
        self.hp = 20
        self.max_hp = 20
        self.speed = 0.8
        self.shoot_cooldown = 1200

class RedMidBoss(Enemy):
    def __init__(self):
        super().__init__()
        self.size = 80
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(RED)
        pygame.draw.rect(self.image, WHITE, self.image.get_rect(), 4)
        self.rect = self.image.get_rect(center=(WIDTH//2, -self.size))
        self.hp = 30
        self.max_hp = 30
        self.speed = 2.0
        self.charge_speed = 10.0
        self.state = "APPROACH" # APPROACH, PAUSE, CHARGE
        self.state_timer = 0
        self.charge_dir = (0, 0)

    def update(self, player_pos):
        current_time = pygame.time.get_ticks()
        
        if self.state == "APPROACH":
            dx = player_pos[0] - self.rect.centerx
            dy = player_pos[1] - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 250:
                self.state = "PAUSE"
                self.state_timer = current_time
            elif dist != 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed
                
        elif self.state == "PAUSE":
            if current_time - self.state_timer > 1000: # 1秒停止
                self.state = "CHARGE"
                self.state_timer = current_time
                dx = player_pos[0] - self.rect.centerx
                dy = player_pos[1] - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist != 0:
                    self.charge_dir = (dx / dist, dy / dist)
                    
        elif self.state == "CHARGE":
            self.rect.x += self.charge_dir[0] * self.charge_speed
            self.rect.y += self.charge_dir[1] * self.charge_speed
            if current_time - self.state_timer > 800: # 0.8秒間突進
                self.state = "APPROACH"

class BigBoss(Enemy):
    def __init__(self):
        super().__init__()
        self.size = 150
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(MAGENTA)
        pygame.draw.rect(self.image, WHITE, self.image.get_rect(), 8)
        self.rect = self.image.get_rect(midbottom=(WIDTH//2, 0)) # 画面のすぐ上に配置
        self.hp = 100
        self.max_hp = 100
        self.speed = 1.8
        self.state = "APPROACH" # APPROACH, PREPARING_AOE, AOE
        self.aoe_timer = 0
        self.aoe_range = 350
        self.charge_duration = 2000 # 2秒溜める

    def update(self, player_pos):
        current_time = pygame.time.get_ticks()

        # 初期入場
        if self.rect.top < 50:
            self.rect.y += 2
            return

        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)

        if self.state == "APPROACH":
            # プレイヤーに向かってゆっくりタックル移動
            if dist != 0:
                self.rect.x += (dx / dist) * self.speed
                self.rect.y += (dy / dist) * self.speed
            
            # 一定距離内に入ったら範囲攻撃の準備へ
            if dist < 220:
                self.state = "PREPARING_AOE"
                self.aoe_timer = current_time

        elif self.state == "PREPARING_AOE":
            # 溜め期間中は少しだけプレイヤーの方へ向き直るが移動は制限
            dx = player_pos[0] - self.rect.centerx
            if abs(dx) > 5:
                self.rect.x += (dx / abs(dx)) * 0.5
            
            if current_time - self.aoe_timer > self.charge_duration:
                self.state = "AOE"
                self.aoe_timer = current_time
        
        elif self.state == "AOE":
            if current_time - self.aoe_timer > 600: # 攻撃判定の持続時間
                self.state = "APPROACH"

class ExpOrb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))
        self.value = 1

    def update(self, player_pos, pickup_range):
        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist < pickup_range and dist != 0:
            self.rect.x += (dx / dist) * 5
            self.rect.y += (dy / dist) * 5

# =====================================
# ゲーム管理クラス
# =====================================

class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player = Player()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.bullets = pygame.sprite.Group()
        self.piercing_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.exp_orbs = pygame.sprite.Group()
        
        self.level = 1
        self.exp = 0
        self.next_level_exp = 5

        # ウェーブ管理の初期化
        self.wave_config = WAVE_CONFIG
        self.current_wave = 1
        self.wave_duration = 45000  # 45秒
        self.wave_start_time = pygame.time.get_ticks()
        self.boss_spawned = False

        # スキル関連の初期化
        self.piercing_count = 0
        self.last_piercing_time = 0
        self.has_pierce_knockback = False

        self.game_over = False
        self.level_up_pending = False
        self.skill_choices = []
        self.enemy_spawn_cooldown = 1500
        self.last_enemy_spawn_time = 0

        for _ in range(random.randint(1, 5)):
            self.spawn_enemy()

    def spawn_enemy(self):
        # ボスウェーブの特殊処理
        is_unique_boss = False
        if self.current_wave == 5 and not self.boss_spawned:
            enemy = RedMidBoss()
            self.boss_spawned = True
            is_unique_boss = True
        elif self.current_wave == 10 and not self.boss_spawned:
            enemy = BigBoss()
            self.boss_spawned = True
            is_unique_boss = True
        elif self.current_wave in [5, 10]:
            # ボス戦中は雑魚敵を少なくする
            config = self.wave_config.get(self.current_wave, DEFAULT_WAVE_SETTING)
            if len(self.enemies) > config["max_enemies"]: return
            enemy = Enemy()
        else:
            # 設定データに基づいた重み付き抽選
            config = self.wave_config.get(self.current_wave, DEFAULT_WAVE_SETTING)
            weights = config["weights"]
            enemy_type = random.choices(
                list(weights.keys()), 
                weights=list(weights.values())
            )[0]

            if enemy_type == "HeavyEnemy":
                enemy = HeavyEnemy()
            elif enemy_type == "ShootingEnemy":
                enemy = ShootingEnemy()
            else:
                enemy = Enemy()

        # プレイヤーとの距離チェック（ユニークなボス以外に適用）
        if not is_unique_boss:
            dist = math.hypot(enemy.rect.centerx - self.player.rect.centerx, 
                              enemy.rect.centery - self.player.rect.centery)
            if dist < 300: # 300ピクセル以内ならスポーンさせない
                return

        # ウェーブ11以降は体力を倍増
        if self.current_wave >= 11:
            enemy.hp *= 2
            enemy.max_hp *= 2

        self.enemies.add(enemy)
        self.all_sprites.add(enemy)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.game_over and event.key == pygame.K_r:
                    self.reset()
                elif self.level_up_pending:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                        idx = event.key - pygame.K_1
                        self.apply_skill(self.skill_choices[idx])
                        self.level_up_pending = False
        return True

    def apply_skill(self, skill):
        if skill == "fire_rate_up":
            self.player.shoot_cooldown = max(200, self.player.shoot_cooldown - 200)
        elif skill == "speed_up":
            self.player.speed += 1
        elif skill == "pierce_bullet":
            self.piercing_count += 1
        elif skill == "barrier":
            self.player.has_barrier = True
        elif skill == "atk_up":
            self.player.atk_multiplier += 0.5
        elif skill == "hp_up":
            self.player.max_hp += 2
            self.player.hp += 2
        elif skill == "heal":
            self.player.hp = min(self.player.max_hp, self.player.hp + int(self.player.max_hp * 0.6))
        elif skill == "exp_range_up":
            self.player.pickup_range += 100
        elif skill == "pierce_knockback":
            self.has_pierce_knockback = True

    def update(self):
        if self.game_over or self.level_up_pending:
            return

        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        # プレイヤー更新
        self.player.update(keys)

        # ウェーブ管理
        time_in_wave = current_time - self.wave_start_time
        if time_in_wave > self.wave_duration:
            self.current_wave += 1
            self.wave_start_time = current_time
            self.boss_spawned = False

        # 射撃処理
        if keys[pygame.K_SPACE] and current_time - self.player.last_shot_time > self.player.shoot_cooldown:
            self.shoot_bullet()
            self.player.last_shot_time = current_time

        # 貫通弾の自動射撃 (5秒おき)
        if self.piercing_count > 0 and current_time - self.last_piercing_time > 5000:
            self.shoot_piercing_bullet()
            self.last_piercing_time = current_time

        # 敵・弾・経験値オーブ更新
        self.enemies.update(self.player.rect.center)
        for enemy in self.enemies:
            if isinstance(enemy, ShootingEnemy) and not isinstance(enemy, BigBoss):
                enemy.shoot(self.player.rect.center, self.enemy_bullets, self.all_sprites)

        self.bullets.update()
        self.piercing_bullets.update()
        self.enemy_bullets.update()
        self.exp_orbs.update(self.player.rect.center, self.player.pickup_range)

        # 敵生成 (ウェーブ設定を使用)
        config = self.wave_config.get(self.current_wave, DEFAULT_WAVE_SETTING)
        max_enemies = config["max_enemies"]
        dynamic_spawn_cooldown = config["spawn_interval"]
        
        if current_time - self.last_enemy_spawn_time > dynamic_spawn_cooldown:
            if len(self.enemies) < max_enemies:
                self.spawn_enemy()
            self.last_enemy_spawn_time = current_time

        # 経験値回収とレベルアップ判定 (メインループへ移動)
        for orb in self.exp_orbs:
            if self.player.rect.colliderect(orb.rect):
                self.exp += orb.value
                orb.kill()

        if self.exp >= self.next_level_exp:
            self.level += 1
            self.exp -= self.next_level_exp
            self.next_level_exp = int(self.next_level_exp * 1.2 + 2)
            self.level_up_pending = True
            
            # スキル抽選のフィルタリング
            available_skills = [s for s in skills if not (s == "barrier" and self.player.has_barrier)]
            # 貫通弾ノックバックの出現条件：貫通弾を1つ以上持っていて、まだノックバックを持っていない
            if self.piercing_count == 0 or self.has_pierce_knockback:
                available_skills = [s for s in available_skills if s != "pierce_knockback"]
            # 重複取得不可スキルの除外（必要に応じて追加可能）
            if self.has_pierce_knockback:
                available_skills = [s for s in available_skills if s != "pierce_knockback"]

            self.skill_choices = random.sample(available_skills, min(3, len(available_skills)))

        # 衝突判定: 弾 vs 敵 (HP制)
        enemy_hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, True)
        for enemy, bullets in enemy_hits.items():
            enemy.hp -= len(bullets) * self.player.atk_multiplier
            self.check_enemy_death(enemy)

        # 衝突判定: 貫通弾 vs 敵
        pierce_hits = pygame.sprite.groupcollide(self.enemies, self.piercing_bullets, False, False)
        for enemy, p_bullets in pierce_hits.items():
            for pb in p_bullets:
                if enemy not in pb.hit_enemies:
                    enemy.hp -= 2 * self.player.atk_multiplier # 攻撃力2倍 * 倍率
                    # ノックバック処理
                    if self.has_pierce_knockback:
                        knockback_power = 40
                        enemy.rect.x += pb.dx * knockback_power
                        enemy.rect.y += pb.dy * knockback_power
                    pb.hit_enemies.add(enemy)
                    self.check_enemy_death(enemy)

        # プレイヤーの被弾判定 (HP制)
        if current_time > self.player.invincible_timer:
            hit_enemies = pygame.sprite.spritecollide(self.player, self.enemies, False)
            hit_bullets = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
            
            # ウェーブ11以降は被ダメージを倍にする
            damage_amount = 2 if self.current_wave >= 11 else 1

            if hit_enemies or hit_bullets:
                if self.player.has_barrier:
                    self.player.has_barrier = False
                    self.player.invincible_timer = current_time + 1000 # 少し無敵
                    return

                self.player.hp -= damage_amount
                self.player.invincible_timer = current_time + 1000 # 1秒の無敵
                
                # ダメージ時の視覚効果（点滅の代わりに一瞬赤くするなど、ここでは簡易的に）
                if self.player.hp <= 0:
                    self.game_over = True

        # 大ボスの近接範囲攻撃ダメージ判定
        for enemy in self.enemies:
            if isinstance(enemy, BigBoss) and enemy.state == "AOE" and current_time > self.player.invincible_timer:
                dist = math.hypot(self.player.rect.centerx - enemy.rect.centerx, self.player.rect.centery - enemy.rect.centery)
                if dist < enemy.aoe_range:
                    self.player.hp -= (2 if self.current_wave >= 11 else 1)
                    self.player.invincible_timer = current_time + 1000
                    self.game_over = True

    def check_enemy_death(self, enemy):
        if enemy.hp <= 0 and enemy.alive():
            # 経験値オーブの生成（ボスは多めに）
            orb_count = 5 if isinstance(enemy, (MidBoss, RedMidBoss)) else 15 if isinstance(enemy, BigBoss) else 1
            for _ in range(orb_count):
                rx = enemy.rect.centerx + random.randint(-20, 20)
                ry = enemy.rect.centery + random.randint(-20, 20)
                orb = ExpOrb(rx, ry)
                self.exp_orbs.add(orb)
                self.all_sprites.add(orb)
            enemy.kill()

    def shoot_bullet(self):
        # 最も近い敵を探す
        closest_enemy = None
        min_dist = float('inf')
        for enemy in self.enemies:
            dist = math.hypot(enemy.rect.centerx - self.player.rect.centerx, 
                              enemy.rect.centery - self.player.rect.centery)
            if dist < min_dist:
                min_dist = dist
                closest_enemy = enemy

        if closest_enemy:
            dx = closest_enemy.rect.centerx - self.player.rect.centerx
            dy = closest_enemy.rect.centery - self.player.rect.centery
            dist = math.hypot(dx, dy)
            if dist != 0:
                bullet = Bullet(self.player.rect.centerx, self.player.rect.centery, dx/dist, dy/dist)
                self.bullets.add(bullet)
                self.all_sprites.add(bullet)

    def shoot_piercing_bullet(self):
        closest_enemy = None
        min_dist = float('inf')
        for enemy in self.enemies:
            dist = math.hypot(enemy.rect.centerx - self.player.rect.centerx, 
                              enemy.rect.centery - self.player.rect.centery)
            if dist < min_dist:
                min_dist = dist
                closest_enemy = enemy

        if closest_enemy:
            dx = closest_enemy.rect.centerx - self.player.rect.centerx
            dy = closest_enemy.rect.centery - self.player.rect.centery
            dist = math.hypot(dx, dy)
            base_angle = math.atan2(dy, dx)
            if dist != 0:
                # piercing_countの分だけ、扇状に弾を同時発射
                for i in range(self.piercing_count):
                    angle_offset = math.radians((i - (self.piercing_count - 1) / 2) * 15) # 15度ずつずらす
                    p_bullet = PiercingBullet(self.player.rect.centerx, self.player.rect.centery, 
                                             math.cos(base_angle + angle_offset), math.sin(base_angle + angle_offset))
                    self.piercing_bullets.add(p_bullet)
                    self.all_sprites.add(p_bullet)

    def draw(self):
        screen.fill(BLACK)
        
        # スプライトの一括描画
        self.exp_orbs.draw(screen)
        self.bullets.draw(screen)
        self.piercing_bullets.draw(screen)
        self.enemy_bullets.draw(screen)
        self.enemies.draw(screen)

        # ボスのHPバー描画
        for enemy in self.enemies:
            if isinstance(enemy, BigBoss):
                hp_ratio = max(0, enemy.hp / enemy.max_hp)
                bar_w, bar_h = 800, 20
                bar_x = (WIDTH - bar_w) // 2
                bar_y = 40
                pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(screen, MAGENTA, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)
                boss_text = small_font.render("GREAT BOSS", True, WHITE)
                screen.blit(boss_text, (bar_x, bar_y - 25))
                hp_num = small_font.render(f"{enemy.hp} / {enemy.max_hp}", True, WHITE)
                screen.blit(hp_num, (bar_x + bar_w - 100, bar_y - 25))
                
                # 近接攻撃の予兆描画
                if enemy.state == "PREPARING_AOE":
                    # 赤い円で範囲を表示（点滅させる）
                    if (pygame.time.get_ticks() // 200) % 2 == 0:
                        pygame.draw.circle(screen, RED, enemy.rect.center, enemy.aoe_range, 3)
                    # 溜めの進捗に合わせて円の太さを変えるなどの演出
                    progress = (pygame.time.get_ticks() - enemy.aoe_timer) / enemy.charge_duration
                    pygame.draw.circle(screen, RED, enemy.rect.center, int(enemy.aoe_range * progress), 1)
                
                # 攻撃瞬間のエフェクト
                elif enemy.state == "AOE":
                    pygame.draw.circle(screen, MAGENTA, enemy.rect.center, enemy.aoe_range, 10)
            
            elif enemy.max_hp > 1:
                # 中ボスや耐久力の高い敵（オレンジなど）のHPバー描画
                hp_ratio = max(0, enemy.hp / enemy.max_hp)
                pygame.draw.rect(screen, BLACK, (enemy.rect.x, enemy.rect.y - 12, enemy.size, 6))
                if isinstance(enemy, MidBoss):
                    bar_color = YELLOW
                elif isinstance(enemy, RedMidBoss):
                    bar_color = RED
                else:
                    bar_color = ORANGE
                
                # 赤色の中ボスが突進準備中の場合、予告線を描画
                if isinstance(enemy, RedMidBoss) and enemy.state == "PAUSE":
                    pygame.draw.line(screen, RED, enemy.rect.center, self.player.rect.center, 2)

                pygame.draw.rect(screen, bar_color, (enemy.rect.x, enemy.rect.y - 12, int(enemy.size * hp_ratio), 6))
                hp_num = small_font.render(f"{enemy.hp}", True, WHITE)
                screen.blit(hp_num, (enemy.rect.x, enemy.rect.y - 30))

        # プレイヤー描画 (無敵時間は点滅させる)
        if pygame.time.get_ticks() > self.player.invincible_timer or (pygame.time.get_ticks() // 100) % 2 == 0:
            screen.blit(self.player.image, self.player.rect)
            # バリアの視覚効果
            if self.player.has_barrier:
                barrier_color = (100, 200, 255, 150) # 水色（半透明っぽく見せるための色）
                pygame.draw.circle(screen, barrier_color, self.player.rect.center, self.player.size, 2)

        # UI: 経験値バー
        pygame.draw.rect(screen, DARK_GRAY, (0, HEIGHT - UI_HEIGHT, WIDTH, UI_HEIGHT))
        exp_ratio = min(1.0, self.exp / self.next_level_exp)
        pygame.draw.rect(screen, GREEN, (0, HEIGHT - UI_HEIGHT, WIDTH * exp_ratio, UI_HEIGHT))
        
        level_text = small_font.render(f"Lv {self.level}  {self.exp}/{self.next_level_exp}", True, WHITE)
        player_hp_text = small_font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, RED if self.player.hp <= 1 else WHITE)
        wave_text = small_font.render(f"WAVE {self.current_wave}", True, WHITE)
        
        # 次のウェーブまでの残り時間
        remaining_time = max(0, (self.wave_duration - (pygame.time.get_ticks() - self.wave_start_time)) // 1000)
        timer_text = small_font.render(f"NEXT WAVE: {remaining_time}s", True, WHITE)
        
        screen.blit(level_text, (10, HEIGHT - UI_HEIGHT + 2))
        screen.blit(player_hp_text, (150, HEIGHT - UI_HEIGHT + 2))
        screen.blit(wave_text, (WIDTH // 2 - 40, HEIGHT - UI_HEIGHT + 2))
        screen.blit(timer_text, (WIDTH - 150, HEIGHT - UI_HEIGHT + 2))

        # レベルアップ画面
        if self.level_up_pending:
            self.draw_overlay("レベルアップ！スキルを選択")
            for i, skill in enumerate(self.skill_choices):
                text = small_font.render(f"{i+1}: {skill_names[skill]}", True, WHITE)
                screen.blit(text, (WIDTH // 2 - 150, HEIGHT // 2 - 50 + i * 60))

        # ゲームオーバー画面
        if self.game_over:
            self.draw_overlay("GAME OVER")
            restart_text = font.render("PRESS R TO RESTART", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(restart_text, restart_rect)

        pygame.display.update()

    def draw_overlay(self, title_str):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        title = font.render(title_str, True, WHITE if not self.game_over else RED)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(title, title_rect)

def main():
    game = Game()
    running = True
    while running:
        running = game.handle_events()
        game.update()
        game.draw()
        clock.tick(60)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()