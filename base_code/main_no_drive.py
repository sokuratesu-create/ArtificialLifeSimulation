# 遺伝子ドライブ組み込みなしのシミュレーション

import pygame
import random
import numpy as np
import matplotlib.pyplot as plt
import csv

from model.organism import Organism

# vscodeではTrue, colabではFalse
VISUALIZE = True

ORG_NUM = 100
FOOD_NUM = 45
FOOD_COLOR = (255, 220, 50)
FOOD_RADIUS = 4
FOOD_EAT_RADIUS = 15
REMAINING_INDIVIDUALS = 10
REPRODUCTION_DISTANCE = 5 #繁殖できる2個体の距離の最大値
REPRODUCTION_COOLDOWN = 45 #各個体の繁殖クールダウンフレーム

# 気温変化の設定
HOT_FRAMES = 500
COLD_FRAMES = 500
HOT_STAMINA_MULTIPLIER = 1.5
COLD_STAMINA_MULTIPLIER = 1.0

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

# 繁殖できてるかの確認のやつ(生き残った個体の数と最大の個体番号を出力)
def print_breeding(org_list):
    print(len(org_list))
    print(max(org.org_id for org in org_list))

#-------------------------------------------------------------------------------------------

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
    plt.ylim(80, 150)
    plt.title("Stamina")
    plt.savefig("stamina.png")
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.scatter([org.org_id for org in org_list], detection_range_values, color="black", marker="o")
    plt.ylim(25, 85)
    plt.title("detection_range")
    plt.savefig("detection.png")
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.scatter([org.org_id for org in org_list], speed_values, color="black", marker="o")
    plt.ylim(0, 4)
    plt.title("speed")
    plt.savefig("speed.png")
    plt.close()

def display_population_graph(population_history):
    frames = [data[0] for data in population_history]
    populations = [data[1] for data in population_history]

    plt.figure(figsize=(10, 6))
    plt.plot(frames, populations, color="black")

    #環境が切り替わるフレーム
    plt.axvline(x=500, color="orange", linestyle="--", label="Enviroment change")
    plt.axvline(x=1000, color="blue", linestyle="--", label="Enviroment change")
    plt.axvline(x=1500, color="orange", linestyle="--", label="Enviroment change")
    plt.axvline(x=2000, color="blue", linestyle="--", label="Enviroment change")

    plt.title("Population over Time")
    plt.xlabel("Frame")
    plt.ylabel("Number of Living Organisms")
    plt.xlim(0, 2000)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig("population.png")
    plt.show()
    plt.close()

#暑さ耐性に関する個体の記録
def record_population_data(org_list, frame):
    population = len(org_list)

    if population == 0:
        avg_heat_tolerance = 0
        std_heat_tolerance = 0
        d_carrier_rate = 0
        d_allele_frequency = 0
    else:
        heat_values = [org.genes["heat_tolerance"] for org in org_list]
        avg_heat_tolerance = float(np.mean(heat_values))
        std_heat_tolerance = float(np.std(heat_values))

        d_carriers = sum(1 for org in org_list if "D" in org.drive_genotype)
        d_carrier_rate = d_carriers / population

        d_allele_count = sum(org.drive_genotype.count("D") for org in org_list)
        d_allele_frequency = d_allele_count / (population * 2)

    return {
        "frame": frame,
        "population": population,
        "avg_heat_tolerance": avg_heat_tolerance,
        "std_heat_tolerance": std_heat_tolerance,
        "d_carrier_rate": d_carrier_rate,
        "d_allele_frequency": d_allele_frequency,
    }

#csvファイルに保存
def save_population_data(history, filename="population_data.csv"):
    fieldnames = [
        "frame",
        "population",
        "avg_heat_tolerance",
        "std_heat_tolerance",
        "d_carrier_rate",
        "d_allele_frequency",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history)

    print(f"記録データを{filename}に保存しました")

#---------------------------------------------------------------------------------------------

def main():
    width, height = 500, 500
    flame_count = 0
    max_flame = 2000
    population_history = []
    simulation_history = []
    gender = [1, 2] # 1:オス, 2:メス
    if VISUALIZE:
        pygame.init()
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Organism Simulation")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 28)

    #初期個体の生成
    org_list = []
    for i in range(ORG_NUM):
        genotype = ["W","W"] 
        org = Organism(i, width, height, random.choice(gender), drive_genotype=genotype)
        org_list.append(org)
    food_list = [Food((random.uniform(0, width), random.uniform(0, height))) for _ in range(FOOD_NUM)]


    while True:
        if VISUALIZE:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                    return

        #体力0の個体は非表示にする
        org_list = [org for org in org_list if org.stamina > 0]

        # 気温を300フレームごとに暑い・寒いと切り替える
        cycle = HOT_FRAMES + COLD_FRAMES
        is_hot = (flame_count % cycle) < HOT_FRAMES
        
        if is_hot:
            stamina_multiplier = HOT_STAMINA_MULTIPLIER
        else:
            stamina_multiplier = COLD_STAMINA_MULTIPLIER

        for org in org_list:
            org.move(food_list, is_hot, HOT_STAMINA_MULTIPLIER, COLD_STAMINA_MULTIPLIER)

        # 繁殖の処理
        new_orgs = []
        for i in range(len(org_list)):
            for j in range(i + 1, len(org_list)):
                if org_list[i].gender == org_list[j].gender:
                    continue

                org_a = org_list[i]
                org_b = org_list[j]

                if np.linalg.norm(org_a.position - org_b.position) <= REPRODUCTION_DISTANCE:
                    if org_a.reproduction_cooldown <= 0 and org_b.reproduction_cooldown <= 0:
                        next_id = max([org.org_id for org in org_list] + [org.org_id for org in new_orgs], default = -1) + 1
                        child = org_a.reproduce(next_id, width, height, random.choice(gender), org_b, flame_count, org_a.drive_genotype, org_b.drive_genotype)
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
                    org.stamina = min(org.genes["stamina"], org.stamina + 25)
                    break
            if not eaten:
                remaining_food.append(food)
        food_list = remaining_food

        # 餌の数が少なくなったら新しい餌を追加
        if len(food_list) < FOOD_NUM:
            food_list.append(Food((random.uniform(0, width), random.uniform(0, height))))

        population_history.append((flame_count, len(org_list)))
        simulation_history.append(record_population_data(org_list, flame_count))

        if VISUALIZE:
            screen.fill((0, 0, 0))

            for food in food_list:
                food.display(screen)

            for org in org_list:
                org.display(screen, flame_count)

            # フレーム数を表示（ここに追加）
            frame_text = font.render(
                f"Frame: {flame_count}", True, (255, 255, 255)
            )
            screen.blit(frame_text, (10, 10))

            pygame.display.flip()
            clock.tick(30)

        flame_count += 1


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
            display_population_graph(population_history)

            #生き残った個体の番号とドライブを保有してるかの情報確認
            ikinokori = [0, 0, 0]
            for org in org_list:     
                #print(f"Org {org.org_id}: {org.drive_genotype}")
                if org.org_id > 99:
                    if org.drive_genotype == ["W","W"]:
                        ikinokori[0] += 1
                    elif org.drive_genotype == ["D","D"]:
                        ikinokori[2] += 1
                    else:
                        ikinokori[1] += 1
            print(f"生き残った個体の遺伝子情報: {ikinokori[0]}WW,{ikinokori[1]}WD/DW,{ikinokori[2]}DD")
            
            pygame.time.wait(1000)

            if VISUALIZE:
                pygame.quit()

            save_population_data(simulation_history)
            return

        


if __name__ == "__main__":
    main()