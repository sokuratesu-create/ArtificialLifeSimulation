import pygame
import random
import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from model.organism import Organism

ORG_NUM = 100
FOOD_NUM = 40
FOOD_COLOR = (255, 220, 50)
FOOD_RADIUS = 4
FOOD_EAT_RADIUS = 15
REMAINING_INDIVIDUALS = 10
REPRODUCTION_DISTANCE = 5
REPRODUCTION_COOLDOWN = 30

class Food:
    def __init__(self, position):
        self.position = np.array(position)

    def display(self, screen):
        pygame.draw.circle(screen, FOOD_COLOR, self.position.astype(int), FOOD_RADIUS)

# 生き残った10個体の遺伝子情報を出力するやつ
"""
def print_final_organisms(org_list):
    len_orgs = len(org_list)
    all_stamina = 0
    all_detection_range = 0
    all_speed = 0
    for org in org_list:
        all_stamina += org.genes["stamina"]
        all_detection_range += org.genes["detection_range"]
        all_speed += org.genes["speed"]
        print(f"Org {org.org_id}: stamina={org.stamina:.2f}, "
              f"genes={org.genes}")
    print(all_stamina / len_orgs, all_detection_range / len_orgs, all_speed / len_orgs)
"""

# 繁殖できてるかの確認のやつ
def print_breeding(org_list):
    print(len(org_list))
    print(max(org.org_id for org in org_list))

# グラフ上に個体の遺伝子を表示する
def display_genes(org_list):
    if len(org_list) == 0:
        print("skipping gene plot")
        return

    stamina_values = []
    detection_range_values = []
    speed_values = []

    for org in org_list:
        stamina_values.append(org.genes["stamina"])
        detection_range_values.append(org.genes["detection_range"])
        speed_values.append(org.genes["speed"])

    plt.figure(figsize=(10, 6))
    plt.scatter([org.org_id for org in org_list], stamina_values, color="black", marker="o")
    plt.title("Stamina")
    print("before show")
    plt.show()
    print("after show")




def main():
    pygame.init()
    width, height = 1000, 1000
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Organism Simulation")
    flame_count = 0
    max_flame = 900

    org_list = [Organism(i, width, height) for i in range(ORG_NUM)]
    food_list = [Food((random.uniform(0, width), random.uniform(0, height))) for _ in range(FOOD_NUM)]

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        #体力0の個体は非表示にする
        org_list = [org for org in org_list if org.stamina > 0]

        for org in org_list:
            org.move(food_list)

        # 繁殖の処理
        new_orgs = []
        for i in range(len(org_list)):
            for j in range(i + 1, len(org_list)):
                org_a = org_list[i]
                org_b = org_list[j]

                if np.linalg.norm(org_a.position - org_b.position) <= REPRODUCTION_DISTANCE:
                    if org_a.reproduction_cooldown <= 0 and org_b.reproduction_cooldown <= 0:
                        next_id = max([org.org_id for org in org_list] + [org.org_id for org in new_orgs], default = -1) + 1
                        child = org_a.reproduce(next_id, width, height, org_b, flame_count)
                        new_orgs.append(child)
                        org_a.reproduction_cooldown = REPRODUCTION_COOLDOWN
                        org_b.reproduction_cooldown = REPRODUCTION_COOLDOWN
                        break
            """
            if new_orgs:
                break
            """

        if new_orgs:
            org_list.extend(new_orgs)


        # 個体が餌に接近したら餌を消す
        remaining_food = []
        for food in food_list:
            eaten = False
            for org in org_list:
                if np.linalg.norm(org.position - food.position) <= FOOD_EAT_RADIUS:
                    eaten = True
                    org.stamina = min(org.genes["stamina"], org.stamina + 20)
                    break
            if not eaten:
                remaining_food.append(food)
        food_list = remaining_food

        # 餌の数が少なくなったら新しい餌を追加
        if len(food_list) < FOOD_NUM:
            food_list.append(Food((random.uniform(0, width), random.uniform(0, height))))

        screen.fill((0, 0, 0))

        for food in food_list:
            food.display(screen)

        for org in org_list:
            org.display(screen, flame_count)

        flame_count += 1

        pygame.display.flip()

        """
        if len(org_list) <= REMAINING_INDIVIDUALS:
            print_final_organisms(org_list)
            pygame.time.wait(1000)
            pygame.quit()
            return
        """

        if flame_count >= max_flame:
            print_breeding(org_list)
            display_genes(org_list)
            pygame.time.wait(1000)
            pygame.quit()
            return

        
        clock.tick(30)


if __name__ == "__main__":
    main()