import pygame
import sys
import random

pygame.init()

# =====================================
# 画面設定
# =====================================

WIDTH = 1280
HEIGHT = 800
#画面下部経験値バーの幅
UI_HEIGHT = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Shooting Game")

clock = pygame.time.Clock()

# =====================================
# フォント
# =====================================

font = pygame.font.SysFont(None, 72)
small_font = pygame.font.SysFont(None, 24)

# =====================================
# 色
# =====================================

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# =====================================
# プレイヤー
# =====================================

player_size = 30
player_speed = 4


# =====================================
# 弾
# =====================================

bullet_width = 8
bullet_height = 8
bullet_speed = 10

bullets = []

# 発射クールタイム
shoot_cooldown = 1000

# 最後に撃った時間
last_shot_time = 0

# 敵スポーン間隔
enemy_spawn_cooldown = 1500

# 最後に敵をスポーンした時間
last_enemy_spawn_time = 0

# =====================================
# 敵
# =====================================

enemy_size = 30
enemy_speed = 1.5

enemies = []

# =====================================
# 経験値
# =====================================

exp_orbs = []

player_level = 1

player_exp = 0

next_level_exp = 5

# =====================================
# Game Over
# =====================================

game_over = False

# =====================================
# 敵生成関数
# =====================================

def create_enemy():

    side = random.randint(0, 3)

    # 上
    if side == 0:

        x = random.randint(0, WIDTH)
        y = -enemy_size

    # 下
    elif side == 1:

        x = random.randint(0, WIDTH)
        y = HEIGHT + enemy_size

    # 左
    elif side == 2:

        x = -enemy_size
        y = random.randint(0, HEIGHT)

    # 右
    else:

        x = WIDTH + enemy_size
        y = random.randint(0, HEIGHT)

    return {
        "x": x,
        "y": y
    }

# =====================================
# リセット関数
# =====================================

def reset_game():

    global player_x
    global player_y
    global bullets
    global enemies
    global game_over
    global player_level
    global player_exp
    global next_level_exp
    global exp_orbs

    # レベル関連リセット
    player_level = 1
    player_exp = 0
    next_level_exp = 5

    # 経験値オーブ削除
    exp_orbs = []

    player_x = WIDTH // 2
    player_y = HEIGHT // 2

    bullets = []

    enemies = []

    for i in range(random.randint(1, 5)):
        enemies.append(create_enemy())

    game_over = False

# =====================================
# 初期化
# =====================================

reset_game()

# =====================================
# メインループ
# =====================================

running = True

while running:

    clock.tick(60)

    # =====================================
    # イベント処理
    # =====================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # Game Over中のリスタート
            if game_over:
                

                if event.key == pygame.K_r:
                    reset_game()

    # =====================================
    # Game Over中は更新停止
    # =====================================

    if not game_over:

        # =====================================
        # キー入力
        # =====================================

        keys = pygame.key.get_pressed()

        current_time = pygame.time.get_ticks()

        # =====================================
        # 射撃
        # =====================================

        if keys[pygame.K_SPACE]:

            if current_time - last_shot_time > shoot_cooldown:

                bullet_x = player_x + player_size / 2
                bullet_y = player_y + player_size / 2

                # 一番近い敵
                closest_enemy = None
                closest_distance = 999999

                for enemy in enemies:

                    dx = (enemy["x"] + enemy_size / 2) - bullet_x
                    dy = (enemy["y"] + enemy_size / 2) - bullet_y

                    distance = (dx ** 2 + dy ** 2) ** 0.5

                    if distance < closest_distance:

                        closest_distance = distance
                        closest_enemy = enemy

                # 敵がいる場合
                if closest_enemy is not None:

                    dx = (closest_enemy["x"] + enemy_size / 2) - bullet_x
                    dy = (closest_enemy["y"] + enemy_size / 2) - bullet_y

                    distance = (dx ** 2 + dy ** 2) ** 0.5

                    if distance != 0:

                        dx = dx / distance
                        dy = dy / distance

                        bullets.append({
                            "x": bullet_x,
                            "y": bullet_y,
                            "dx": dx,
                            "dy": dy
                        })

                        last_shot_time = current_time

        # =====================================
        # プレイヤー移動
        # =====================================

        if keys[pygame.K_LEFT]:
            player_x -= player_speed

        if keys[pygame.K_RIGHT]:
            player_x += player_speed

        if keys[pygame.K_UP]:
            player_y -= player_speed

        if keys[pygame.K_DOWN]:
            player_y += player_speed

        # =====================================
        # 画面外制限
        # =====================================

        if player_x < 0:
            player_x = 0

        if player_x > WIDTH - player_size:
            player_x = WIDTH - player_size

        if player_y < 0:
            player_y = 0

        if player_y > HEIGHT - player_size:
            player_y = HEIGHT - player_size

        # =====================================
        # 弾移動
        # =====================================

        for bullet in bullets:

            bullet["x"] += bullet["dx"] * bullet_speed
            bullet["y"] += bullet["dy"] * bullet_speed

        # =====================================
        # 画面外弾削除
        # =====================================

        bullets = [
            bullet for bullet in bullets
            if (
                bullet["x"] > -100
                and bullet["x"] < WIDTH + 100
                and bullet["y"] > -100
                and bullet["y"] < HEIGHT + 100
            )
        ]

        # =====================================
        # 敵移動
        # =====================================

        for enemy in enemies:

            dx = player_x - enemy["x"]
            dy = player_y - enemy["y"]

            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance != 0:

                dx = dx / distance
                dy = dy / distance

                enemy["x"] += dx * enemy_speed
                enemy["y"] += dy * enemy_speed


        # =====================================
        # 経験値オーブ吸引
        # =====================================

        for orb in exp_orbs:

            dx = player_x - orb["x"]
            dy = player_y - orb["y"]

            distance = (dx ** 2 + dy ** 2) ** 0.5

            # 近づいたら吸引
            if distance < 100:

                if distance != 0:

                    dx = dx / distance
                    dy = dy / distance

                    orb["x"] += dx * 5
                    orb["y"] += dy * 5

        # =====================================
        # 経験値回収
        # =====================================

        for orb in exp_orbs[:]:

            dx = player_x - orb["x"]
            dy = player_y - orb["y"]

            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance < 20:

                player_exp += orb["value"]

                exp_orbs.remove(orb)

        # =====================================
        # レベルアップ
        # =====================================

        if player_exp >= next_level_exp:

            player_level += 1

            player_exp = player_exp - next_level_exp

            next_level_exp = int(next_level_exp * 1.2 + 2)

            print("LEVEL UP!")


        # =====================================
        # 時間経過で敵スポーン
        # =====================================

        if current_time - last_enemy_spawn_time > enemy_spawn_cooldown:

            # 最大5体まで
            if len(enemies) < 5:

                enemies.append(create_enemy())

            last_enemy_spawn_time = current_time

        # =====================================
        # 当たり判定
        # =====================================

        for bullet in bullets[:]:

            bullet_x = bullet["x"]
            bullet_y = bullet["y"]

            for enemy in enemies[:]:

                if (
                    bullet_x > enemy["x"]
                    and bullet_x < enemy["x"] + enemy_size
                    and bullet_y > enemy["y"]
                    and bullet_y < enemy["y"] + enemy_size
                ):
                    

                    # 経験値オーブ生成
                    exp_orbs.append({
                        "x": enemy["x"],
                        "y": enemy["y"],
                        "value": 1
                    })

                    enemies.remove(enemy)

                    if bullet in bullets:
                        bullets.remove(bullet)

                    break

        # =====================================
        # プレイヤー接触判定（中心距離）
        # =====================================

        for enemy in enemies:

            # 中心座標
            player_cx = player_x + player_size / 2
            player_cy = player_y + player_size / 2

            enemy_cx = enemy["x"] + enemy_size / 2
            enemy_cy = enemy["y"] + enemy_size / 2

            # 距離
            dx = player_cx - enemy_cx
            dy = player_cy - enemy_cy

            distance = (dx ** 2 + dy ** 2) ** 0.5

            # 当たり判定（円）
            if distance < (player_size / 2 + enemy_size / 2):

                game_over = True

    # =====================================
    # 描画
    # =====================================

    screen.fill(BLACK)

    # プレイヤー
    pygame.draw.rect(
        screen,
        WHITE,
        (
            player_x,
            player_y,
            player_size,
            player_size
        )
    )

    # 弾
    for bullet in bullets:

        pygame.draw.circle(
            screen,
            WHITE,
            (int(bullet["x"]), int(bullet["y"])),
            4
        )

    # 敵
    for enemy in enemies:

        pygame.draw.rect(
            screen,
            RED,
            (
                enemy["x"],
                enemy["y"],
                enemy_size,
                enemy_size
            )
        )
    
    # 経験値オーブ
    for orb in exp_orbs:

        pygame.draw.circle(
            screen,
            (0, 255, 0),
            (int(orb["x"]), int(orb["y"])),
            5
        )

    # =====================================
    # 経験値バー
    # =====================================

    # 背景バー
    pygame.draw.rect(
        screen,
        (50, 50, 50),
        (0, HEIGHT - UI_HEIGHT, WIDTH, UI_HEIGHT)
    )

    # 進捗割合
    exp_ratio = player_exp / next_level_exp

    # 実際のバー
    pygame.draw.rect(
        screen,
        (0, 200, 0),
        (
            0,
            HEIGHT - UI_HEIGHT,
            WIDTH * exp_ratio,
            UI_HEIGHT
        )
    )

    # レベル表示
    level_text = small_font.render(
        f"Lv {player_level}  {player_exp}/{next_level_exp}",
        True,
        WHITE
    )

    screen.blit(level_text, (10, HEIGHT - UI_HEIGHT + 2))


    # =====================================
    # GAME OVER表示
    # =====================================

    if game_over:
        # 半透明の黒画面
        overlay = pygame.Surface((WIDTH, HEIGHT))

        overlay.set_alpha(180)

        overlay.fill(BLACK)

        screen.blit(overlay, (0, 0))

        game_over_text = font.render(
            "GAME OVER",
            True,
            RED
        )

        restart_text = font.render(
            "PRESS R TO RESTART",
            True,
            WHITE
        )

        screen.blit(game_over_text, (400, 250))
        screen.blit(restart_text, (250, 350))

    pygame.display.update()

pygame.quit()
sys.exit()