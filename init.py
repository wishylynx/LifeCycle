import pygame
import random
import math
import time

# Класс для водоемов
class WaterPool:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self, screen):
        pygame.draw.circle(screen, pygame.Color("#3498db"), (self.x, self.y), self.radius)

#Глобальные переменные
ATTACK_RANGE = 10
deer_image = pygame.transform.scale(pygame.image.load("images/deer.png"), (30, 30))
wolf_image = pygame.transform.scale(pygame.image.load("images/wolf.png"), (30, 30))
tiger_image = pygame.transform.scale(pygame.image.load("images/tiger.png"), (30, 30))


# Базовый класс для животных
class Animal:
    def __init__(self, x, y, hp, color):
        self.x = x
        self.y = y
        self.hp = hp
        self.color = color
        self.coins = 0  # Инициализация LC-Coin
        self.is_alive = True
        self.angle = random.uniform(0, 2 * math.pi)  # Угол в радианах
        self.base_speed = 1  # Базовая скорость
        self.speed = self.base_speed  # Текущая скорость
        self.last_run_time = 0
        self.view_angle = math.radians(40)  # Угол зрения в радианах
        self.view_distance = 100  # Дальность зрения
        self.target_angle = self.angle
        self.rotation_speed = 0.05
        self.needs_to_run = False
        self.predator = False
        self.attack_speed = 1.5
        self.last_attack_time = 0
        self.last_attacker = None
        self.level = 1


    def change_direction(self):
        if random.random() < 0.005:
            self.target_angle = random.uniform(0, 2 * math.pi)

    def earn_coins(self, amount):
        self.coins += amount

    def is_border_in_view(self):
        # Проверка каждой стороны холста
        for angle in [self.angle - self.view_angle / 2, self.angle + self.view_angle / 2]:
            end_x = self.x + self.view_distance * math.cos(angle)
            end_y = self.y + self.view_distance * math.sin(angle)
            if end_x < 0 or end_x > 1280 or end_y < 0 or end_y > 540:
                return True
        return False

    def predator_in_view(self, animals):
        for animal in animals:
            if animal.predator and self.is_in_view(animal):
                return True
        return False

    def find_nearest_target(self, animals, target_predicate):
        nearest_target = None
        min_distance = float('inf')
        for animal in animals:
            if target_predicate(animal) and self.is_in_view(animal):
                distance = self.calculate_distance(animal)
                if distance < min_distance:
                    min_distance = distance
                    nearest_target = animal
        return nearest_target


    def is_in_view(self, other):
        # Расчет расстояния до другого животного
        distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        if distance > self.view_distance:
            return False  # Животное вне зоны видимости

        # Расчет угла к другому животному
        angle_to_other = math.atan2(other.y - self.y, other.x - self.x)
        angle_diff = (angle_to_other - self.angle + math.pi) % (2 * math.pi) - math.pi

        # Проверка, находится ли другое животное в пределах угла зрения
        return abs(angle_diff) <= self.view_angle / 2

    def calculate_distance(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y)  ** 2)



    def run(self, animals):
        # Собираем положения всех хищников в поле зрения
        predators_positions = [(animal.x, animal.y) for animal in animals if animal.predator and self.is_in_view(animal)]

        if predators_positions:
            # Рассчитываем среднее направление от всех хищников
            avg_x = sum(x for x, _ in predators_positions) / len(predators_positions)
            avg_y = sum(y for _, y in predators_positions) / len(predators_positions)

            # Определяем направление для бегства
            direction_x = self.x - avg_x
            direction_y = self.y - avg_y
            self.target_angle = math.atan2(direction_y, direction_x)
            self.angle = self.target_angle

        new_speed = self.speed * 1.2
        self.speed = min(new_speed, self.base_speed * 1.4)
        self.last_run_time = time.time()

    def update_speed(self):
        # Если прошло 5 секунд после бегства, возвращаем скорость к нормальной
        if time.time() - self.last_run_time > 5:
            self.speed = self.base_speed

    def increase_speed_for_chase(self):
        # Увеличиваем скорость на 10%
        if self.speed < self.base_speed * 1.1:
            self.speed = self.base_speed * 1.1
            self.last_run_time = time.time()


    def move(self, animals):
        # Первый приоритет: если видим границу, меняем направление
        if self.is_border_in_view():
            self.target_angle = random.uniform(0, 2 * math.pi)
            self.angle = self.target_angle  # Немедленно меняем направление
        # Второй приоритет: если не являемся хищником и видим хищника

        elif not self.predator and self.predator_in_view(animals):
            self.run(animals)

        # Ответ на атаку: если являемся хищником и были атакованы
        elif self.predator and self.last_attacker:
            # Проверяем, что обидчик не является тем же видом, что и хищник
            if not isinstance(self.last_attacker, self.__class__):
                # Если обидчик все еще в поле зрения и жив, продолжаем его преследовать
                if self.last_attacker in animals and self.is_in_view(self.last_attacker):
                    self.target_angle = math.atan2(self.last_attacker.y - self.y, self.last_attacker.x - self.x)
                else:
                    self.last_attacker = None  # Сбросим, если атакующий теряется из виду или умирает

        # Третий приоритет: для хищников - направление к другому хищнику другого вида
        elif self.predator:
            nearest_predator = self.find_nearest_target(animals, lambda a: a.predator and a != self and not isinstance(a, self.__class__))
            if nearest_predator:
                self.target_angle = math.atan2(nearest_predator.y - self.y, nearest_predator.x - self.x)
                self.increase_speed_for_chase()
            # Четвертый приоритет: для хищников - направление к непредатору
            else:
                nearest_non_predator = self.find_nearest_target(animals, lambda a: not a.predator)
                if nearest_non_predator:
                    self.target_angle = math.atan2(nearest_non_predator.y - self.y, nearest_non_predator.x - self.x)
                    self.increase_speed_for_chase()  # Увеличиваем скорость для преследования
        # Рассчитываем разницу между текущим и целевым углами
        angle_diff = (self.target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi



        # Плавно меняем угол
        if abs(angle_diff) > self.rotation_speed:
            self.angle += math.copysign(self.rotation_speed, angle_diff)

        # Обновление положения на основе угла и скорости
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

        # Случайная смена направления, если не сработали приоритеты
        self.change_direction()


    def draw_vision_cone(self, screen):
        vision_surface = pygame.Surface((1280, 540), pygame.SRCALPHA)

        # Расчёт точек для отрисовки сектора зрения
        start_angle = self.angle - self.view_angle / 2
        end_angle = self.angle + self.view_angle / 2
        points = [(self.x, self.y)]
        for angle in [start_angle, end_angle]:
            end_x = self.x + self.view_distance * math.cos(angle)
            end_y = self.y + self.view_distance * math.sin(angle)
            points.append((end_x, end_y))
        points.append((self.x, self.y))

        vision_color = pygame.Color("#73C4F2")
        vision_color.a = 80
        pygame.draw.polygon(vision_surface, vision_color, points)

        screen.blit(vision_surface, (15, 15))




    def take_damage(self, amount, attacker):
        #print(f"{self.__class__.__name__} получил урон: {amount}")
        self.hp -= amount
        if self.hp <= 0:
            self.die()
        self.last_attacker = attacker

    def die(self):
        # Здесь логика для обработки смерти животного
        self.is_alive = False
        print(f"=======Животное умерло {self.__class__.__name__}")

    def draw(self, screen):
        self.draw_vision_cone(screen)

        screen.blit(self.image, (self.x, self.y))

        # Отображение здоровья, коинов, уровня, урона (если есть) и скорости
        font = pygame.font.SysFont(None, 24)
        speed_percent = int((self.speed / self.base_speed) * 100)  # Процент скорости
        info_text = f"Lvl: {self.level} HP: {self.hp}"

        # Добавляем урон в отображение только для хищников
        if hasattr(self, 'damage'):
            info_text += f" Dmg: {self.damage}"

        info_text += f" Speed: {speed_percent} %"

        # Отображение кулдауна для хищников
        if self.predator:
            cooldown = max(0, round(self.attack_speed - (time.time() - self.last_attack_time), 1))
            cooldown_color = pygame.Color('#9B111E') if cooldown > 0 else pygame.Color('#1DDD1D')
            cooldown_text = f" CD: {cooldown}"
            cooldown_surface = font.render(cooldown_text, True, cooldown_color)
            screen.blit(cooldown_surface, (self.x + 30, self.y + 15))

        info_surface = font.render(info_text, True, pygame.Color('white'))
        screen.blit(info_surface, (self.x + 35, self.y - 0))


    def engage_in_battle(self, target):
        if isinstance(target, Animal):
            target.take_damage(self.damage)
            if target.hp <= 0:
                self.earn_coins(5)

class Wolf(Animal):
    def __init__(self, x, y):
        super().__init__(x, y, 150, pygame.Color("#BBBBBB"))  # HP и цвет для волков
        self.image = wolf_image
        self.max_hp = 150
        self.max_damage = 100
        self.level = 1
        self.damage = 75  # Урон для волков
        self.pack_bonus = False
        self.predator = True
        self.attack_speed = 1.5
        self.last_attack_time = 0

    def update(self, animals):
        pack_members = sum(1 for animal in animals if isinstance(animal, Wolf) and self.distance(animal) < 10)
        if 0 < pack_members <= 3:
            self.pack_bonus = True
            self.earn_coins(1)
        else:
            self.pack_bonus = False
        for animal in animals:
            if isinstance(animal, Tiger) and self.distance(animal) < ATTACK_RANGE:
                self.attack(animal)

    def distance(self, other_animal):
        return ((self.x - other_animal.x) ** 2 + (self.y - other_animal.y) ** 2) ** 0.5

    def attack(self, target):
        current_time = time.time()
        if current_time - self.last_attack_time >= self.attack_speed and self.distance(target) < ATTACK_RANGE and target != Wolf:
            target.take_damage(self.damage, self)  # self - атакующий
            self.last_attack_time = current_time

            # Если цель умирает и является оленем, восстанавливаем здоровье полностью
            if isinstance(target, Deer) and target.hp <= 0:
                self.hp = self.max_hp

            # Если цель умирает и является конкурентом (не олень)
            elif isinstance(target, Tiger) and target.hp <= 0:
                self.hp = min(self.hp + 100, self.max_hp)  # Восстановление здоровья, но не более максимального
                self.damage = min(self.damage + 15, self.max_damage)  # Увеличение урона, но не более максимального
                self.level = min(self.level + 1, 5)
                self.max_hp = min(self.max_hp + 25, 200)



class Tiger(Animal):
    def __init__(self, x, y):
        super().__init__(x, y, 300, pygame.Color("#FF8E0D"))  # HP и цвет для тигров
        self.image = tiger_image
        self.max_hp = 300
        self.max_damage = 150
        self.level = 1
        self.damage = 90  # Урон для тигров
        self.predator = True
        self.attack_speed = 2
        self.last_attack_time = 0


    def update(self, animals):
        if any(isinstance(animal, Tiger) and self.distance(animal) < 50 for animal in animals):
            self.coins = max(self.coins - 1, 0)  # Предотвращение отрицательного количества коинов
        for animal in animals:
            if isinstance(animal, Wolf) and self.distance(animal) < ATTACK_RANGE:
                self.attack(animal)


    def distance(self, other_animal):
        return ((self.x - other_animal.x) ** 2 + (self.y - other_animal.y) ** 2) ** 0.5

    def attack(self, target):
        current_time = time.time()
        if current_time - self.last_attack_time >= self.attack_speed and self.distance(target) < ATTACK_RANGE and target != Tiger:
            target.take_damage(self.damage, self)  # self - атакующий
            self.last_attack_time = current_time

            # Если цель умирает и является оленем, восстанавливаем здоровье полностью
            if isinstance(target, Deer) and target.hp <= 0:
                self.hp = self.max_hp

            # Если цель умирает и является конкурентом (не олень)
            elif isinstance(target, Wolf) and target.hp <= 0:
                self.hp = min(self.hp + 50, self.max_hp)  # Восстановление здоровья, но не более максимального
                self.damage = min(self.damage + 10, self.max_damage)  # Увеличение урона, но не более максимального
                self.level = min(self.level + 1, 5)
                self.max_hp = min(self.max_hp + 20, 400)

class Deer(Animal):
    def __init__(self, x, y):
        super().__init__(x, y, 125, pygame.Color("#785840"))  # HP и цвет для оленей
        self.image = deer_image

    def dodge_attack(self):
        # 50% шанс увернуться от атаки
        if random.random() < 0.5:
            self.earn_coins(1) # Начисление коина за успешный уворот
            return True
        return False

    def distance(self, other_animal):
        return ((self.x - other_animal.x) ** 2 + (self.y - other_animal.y) ** 2) ** 0.5

    def update(self, animals):
        # Проверка на атаки от хищников и попытка уворота
        for animal in animals:
            if isinstance(animal, (Wolf, Tiger)) and self.distance(animal) < 50:
                if not self.dodge_attack():
                    # Если уворот не удался, получаем урон
                    animal.attack(self)




# Функция для создания начальных объектов
def create_initial_objects():
    water_pools = [WaterPool(random.randint(100, 1180), random.randint(100, 440), 30) for _ in range(5)]

    # Создание животных с учетом их характеристик
    animals = []
    for _ in range(7):  # Примерное количество каждого вида
        # Создание волков
        animals.append(Wolf(random.randint(0, 1280), random.randint(0, 540)))

    for _ in range(3):
        # Создание тигров

        animals.append(Tiger(random.randint(0, 1280), random.randint(0, 540)))

    for _ in range(8):
        # Создание оленей
        animals.append(Deer(random.randint(0, 1280), random.randint(0, 540)))

    return water_pools, animals