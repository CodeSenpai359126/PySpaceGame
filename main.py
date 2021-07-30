import os.path

import random
import sys
import xml.etree.ElementTree as ET

from timeloop import Timeloop
from datetime import timedelta

import pygame

pygame.init()

ran = random.Random()
tl = Timeloop()

WIDTH, HEIGHT = 900, 500
FPS = 60

spawn_enemy = pygame.USEREVENT + 1
spaceship_hit = pygame.USEREVENT + 2
score_add = pygame.USEREVENT + 3

SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 35, 35
VEL = 6
SPACESHIP_MAX_BULLETS = 4
SPACESHIP_MAX_HEALTH = 10
spaceship_bullets = []

ENEMY_WIDTH, ENEMY_HEIGHT = 55, 55
VEL_ENEMY = 1
enemies = []
enemy_bullets = []
SPAWN_INTERVAL = 2
FIRE_INTERVAL = 1.2

VEL_BULLETS = 8

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)

END_FONT = pygame.font.SysFont("comicsans", 100)
NORM_FONT = pygame.font.SysFont("comicsans", 40)
SMALL_NORM_FONT = pygame.font.SysFont("comicsans", 30)

ENEMY_IMAGE = pygame.image.load(os.path.join('Assets', 'Default', 'enemy_D.png'))
ENEMY = pygame.transform.rotate((pygame.transform.scale(ENEMY_IMAGE, (ENEMY_WIDTH, ENEMY_HEIGHT))), 90)
SPACESHIP_IMAGE = pygame.image.load(os.path.join('Assets', 'Default', 'ship_G.png'))
SPACESHIP = pygame.transform.rotate(pygame.transform.scale(SPACESHIP_IMAGE, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 270)

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Test Game")

FILE_NAME = 'scoreboard.xml'
dom = ET.parse(FILE_NAME)
root = dom.getroot()


player = dom.findall('player')


def draw_window(spaceship, spaceship_bullets, enemies, enemy_bullets, score, health):
    score_text = f"score: {score}"
    health_text = f"health: {health}/{SPACESHIP_MAX_HEALTH}"
    draw_text = NORM_FONT.render(score_text, True, WHITE)
    draw_text2 = NORM_FONT.render(health_text, True, WHITE)
    WIN.fill(BLACK)
    WIN.blit(draw_text, (20, 20))
    WIN.blit(draw_text2, (WIDTH - 20 - draw_text2.get_width(), 20))
    WIN.blit(SPACESHIP, (spaceship.x, spaceship.y))
    for bullet in spaceship_bullets:
        pygame.draw.rect(WIN, BLUE, bullet)
    for enemy in enemies:
        WIN.blit(ENEMY, (enemy.x, enemy.y))
    for bullet in enemy_bullets:
        pygame.draw.rect(WIN, RED, bullet)
    pygame.display.update()


def draw_end_text(scoreboard, score):
    y = 140
    place = 1
    draw_text = END_FONT.render("GAME OVER", True, WHITE)
    draw2_text = NORM_FONT.render(f"Your score {score}", True, WHITE)
    WIN.blit(draw_text, (WIDTH / 2 - draw_text.get_width() / 2, 20))
    WIN.blit(draw2_text, (WIDTH / 2 - draw2_text.get_width() / 2, 100))
    for p in scoreboard:
        draw_scoreboard = NORM_FONT.render(f"{place}. {p.get('name')} - {p.get('score')}", True, WHITE)
        WIN.blit(draw_scoreboard, (WIDTH / 2 - draw_scoreboard.get_width() / 2, y))
        y += 40
        place += 1
    pygame.display.update()
    pygame.time.delay(5000)


def control_spaceship(spaceship):
    keys_pressed = pygame.key.get_pressed()
    if keys_pressed[pygame.K_w] and not spaceship.y - VEL < 0:  # Up
        spaceship.y -= VEL
    if keys_pressed[pygame.K_s] and not spaceship.y + SPACESHIP_HEIGHT + VEL > HEIGHT:  # Down
        spaceship.y += VEL
    if keys_pressed[pygame.K_a] and not spaceship.x - VEL < 0:  # Left
        spaceship.x -= VEL
    if keys_pressed[pygame.K_d] and not spaceship.x + SPACESHIP_WIDTH + VEL > WIDTH:  # Right
        spaceship.x += VEL


def handle_enemies(enemies):
    for enemy in enemies:
        enemy.x -= VEL_ENEMY


@tl.job(interval=timedelta(seconds=SPAWN_INTERVAL))
def spawn_enemy():
    enemy = pygame.Rect(WIDTH - 20, ran.randint(20, (HEIGHT - 70)), ENEMY_WIDTH, ENEMY_HEIGHT)
    enemies.append(enemy)


@tl.job(interval=timedelta(seconds=FIRE_INTERVAL))
def enemy_fire():
    for enemy in enemies:
        enemy_bullet = pygame.Rect(enemy.x + ENEMY_WIDTH, enemy.y + ENEMY_HEIGHT / 2 - 2, 10, 5)
        enemy_bullets.append(enemy_bullet)


def handle_bullets(spaceship_bullets, enemy_bullets, spaceship, enemies):
    for bullet in spaceship_bullets:
        bullet.x += VEL_BULLETS
        if bullet.x > WIDTH:
            spaceship_bullets.remove(bullet)
        for enemy in enemies:
            if enemy.colliderect(bullet):
                spaceship_bullets.remove(bullet)
                enemies.remove(enemy)
                pygame.event.post(pygame.event.Event(score_add))
    for bullet in enemy_bullets:
        bullet.x -= VEL_BULLETS
        if bullet.x < 0:
            enemy_bullets.remove(bullet)
        elif spaceship.colliderect(bullet):
            enemy_bullets.remove(bullet)
            pygame.event.post(pygame.event.Event(spaceship_hit))


def name_input():
    user_text = ''
    input_rect = pygame.Rect(200, 200, (WIDTH / 2) - 200, (HEIGHT / 2) - 200)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                elif event.key == pygame.K_KP_ENTER:
                    return user_text
                else:
                    user_text += event.unicode

        pygame.draw.rect(WIN, GRAY, input_rect)
        text_surface = SMALL_NORM_FONT.render(user_text, True, BLACK)
        WIN.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
        input_rect.w = max(100, text_surface.get_width() + 10)
        pygame.display.flip()


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def edit_XML(score, name):
    scoreboard = []
    run_XML = True
    old_score = 0
    old_name = ""
    for elem in root.iter('player'):
        if score > int(elem.get('score')) and run_XML:
            old_score = int(elem.get('score'))
            old_name = elem.get('name')
            elem.set('score', str(score))
            elem.set('name', name)
            run_XML = False
            dom.write('scoreboard.xml')
        elif old_score > int(elem.get('score')):
            temp_score = int(elem.get('score'))
            temp_name = elem.get('name')
            elem.set('score', str(old_score))
            elem.set('name', old_name)
            dom.write('scoreboard.xml')
            old_score = temp_score
            old_name = temp_name

    for p in player:
        scoreboard.append(p)
    return scoreboard


def main():
    spaceship = pygame.Rect(20, HEIGHT // 2, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)

    score = 0
    spaceship_health = SPACESHIP_MAX_HEALTH

    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and len(spaceship_bullets) < SPACESHIP_MAX_BULLETS:
                    bullet = pygame.Rect(spaceship.x + SPACESHIP_WIDTH, spaceship.y + SPACESHIP_HEIGHT / 2 - 2, 10, 5)
                    spaceship_bullets.append(bullet)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                    pygame.quit()
                    sys.exit()
            if event.type == spaceship_hit:
                spaceship_health -= 1
            if event.type == score_add:
                score += 1
        if spaceship_health <= 0:
            tl.stop()
            name = name_input()
            scoreboard = edit_XML(score, name)
            draw_end_text(scoreboard, score)
            pygame.quit()
            sys.exit()

        control_spaceship(spaceship)
        handle_enemies(enemies)
        handle_bullets(spaceship_bullets, enemy_bullets, spaceship, enemies)
        draw_window(spaceship, spaceship_bullets, enemies, enemy_bullets, score, spaceship_health)


if __name__ == "__main__":
    tl.start()
    main()
