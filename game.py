import pygame
from init import create_initial_objects
import requests





#Инициализация Pygame и создание окна
pygame.init()
screen = pygame.display.set_mode((1280, 540))
pygame.display.set_caption("Жизненный Цикл Животных")
background_color = pygame.Color("#71BC78")  # Зеленый фон

#Создание водоемов и животных
water_pools, animals = create_initial_objects()


#Игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(background_color)  # Заполнение фона

    for pool in water_pools:  # Отрисовка водоемов
        pool.draw(screen)

    for animal in animals:  # Перемещение и отрисовка животных
        animal.update_speed()
        animal.move(animals)
        animal.update(animals)
        animal.draw(screen)
        animals = [animal for animal in animals if animal.is_alive]
    pygame.display.flip()  # Обновление экрана

pygame.quit()



'''

def get_game_state():
    response = requests.get("http://localhost:5000/get_game_state")
    return response.json()

def update_game_state(data):
    response = requests.post("http://localhost:5000/update_game_state", json=data)
    return response.json()

def save_game_state():
    # Предполагается, что у вас есть переменная game_state с текущим состоянием игры
    response = requests.post("http://localhost:5000/save_game", json=game_state)
    print(response.json())

def load_game_state():
    response = requests.get("http://localhost:5000/load_game")
    game_state = response.json()
    # Обновите состояние игры на основе полученных данных
    '''