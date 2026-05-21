import pygame
import sys
import random
import math

pygame.init()

# =====================================
# 設定・定数
# =====================================
WIDTH = 1280
HEIGHT = 800
UI_HEIGHT = 25
XP_BAR_HEIGHT = 30

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
DARK_GRAY = (50, 50, 50)

skills = [
    "fire_rate_up",
    "bullet_count_up",
    "speed_up"
]

skill_names = {
    "fire_rate_up": "連射速度アップ",
    "bullet_count_up": "弾数増加",
    "speed_up": "移動速度アップ"
}

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
        self.speed = 10

    def update(self):
        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed
        if not screen.get_rect().inflate(200, 200).contains(self.rect):
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
        if not screen.get_rect().contains(self.rect):
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(RED)
        
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

class ShootingEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.image.fill(YELLOW)
        self.shoot_cooldown = 2000
        self.last_shot_time = pygame.time.get_ticks() + random.randint(0, 1000)

    def shoot(self, player_pos, enemy_bullets, all_sprites):
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

class ExpOrb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))
        self.value = 1

    def update(self, player_pos):
        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist < 100 and dist != 0:
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
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.exp_orbs = pygame.sprite.Group()
        
        self.level = 1
        self.exp = 0
        self.next_level_exp = 5
        self.game_over = False
        self.level_up_pending = False
        self.skill_choices = []
        self.enemy_spawn_cooldown = 1500
        self.last_enemy_spawn_time = 0

        for _ in range(random.randint(1, 5)):
            self.spawn_enemy()

    def spawn_enemy(self):
        if random.random() < 0.3:  # 30%の確率で射撃タイプを生成
            enemy = ShootingEnemy()
        else:
            enemy = Enemy()
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
        # bullet_count_up は現状の実装を維持

    def update(self):
        if self.game_over or self.level_up_pending:
            return

        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        # プレイヤー更新
        self.player.update(keys)

        # 射撃処理
        if keys[pygame.K_SPACE] and current_time - self.player.last_shot_time > self.player.shoot_cooldown:
            self.shoot_bullet()
            self.player.last_shot_time = current_time

        # 敵・弾・経験値オーブ更新
        self.enemies.update(self.player.rect.center)
        for enemy in self.enemies:
            if isinstance(enemy, ShootingEnemy):
                enemy.shoot(self.player.rect.center, self.enemy_bullets, self.all_sprites)

        self.bullets.update()
        self.enemy_bullets.update()
        self.exp_orbs.update(self.player.rect.center)

        # 敵生成
        if current_time - self.last_enemy_spawn_time > self.enemy_spawn_cooldown:
            if len(self.enemies) < 5:
                self.spawn_enemy()
            self.last_enemy_spawn_time = current_time

        # 衝突判定: 弾 vs 敵
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for enemy_hit in hits:
            orb = ExpOrb(enemy_hit.rect.centerx, enemy_hit.rect.centery)
            self.exp_orbs.add(orb)
            self.all_sprites.add(orb)

        # 経験値回収
        for orb in self.exp_orbs:
            if self.player.rect.colliderect(orb.rect):
                self.exp += orb.value
                orb.kill()

        # レベルアップ判定
        if self.exp >= self.next_level_exp:
            self.level += 1
            self.exp -= self.next_level_exp
            self.next_level_exp = int(self.next_level_exp * 1.2 + 2)
            self.level_up_pending = True
            self.skill_choices = random.sample(skills, 3)

        # 敗北判定
        if pygame.sprite.spritecollide(self.player, self.enemies, False, pygame.sprite.collide_circle):
            self.game_over = True
            
        # 敵の弾による敗北判定
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_circle):
            self.game_over = True

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

    def draw(self):
        screen.fill(BLACK)
        
        # スプライトの一括描画
        self.exp_orbs.draw(screen)
        self.bullets.draw(screen)
        self.enemy_bullets.draw(screen)
        self.enemies.draw(screen)
        screen.blit(self.player.image, self.player.rect)

        # UI: 経験値バー
        pygame.draw.rect(screen, DARK_GRAY, (0, HEIGHT - UI_HEIGHT, WIDTH, UI_HEIGHT))
        exp_ratio = min(1.0, self.exp / self.next_level_exp)
        pygame.draw.rect(screen, GREEN, (0, HEIGHT - UI_HEIGHT, WIDTH * exp_ratio, UI_HEIGHT))
        
        level_text = small_font.render(f"Lv {self.level}  {self.exp}/{self.next_level_exp}", True, WHITE)
        screen.blit(level_text, (10, HEIGHT - UI_HEIGHT + 2))

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