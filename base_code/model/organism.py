import pygame
import random
import numpy as np

#個体が進む方向の範囲
RANGE_OF_DIRECTIONS = [0, 360]

#個体の色リスト
ORGANISM_COLORS = ['#FFA5CC', '#A0D4FF']

#体力の定数(min, max)
STAMINA_MIN = 75
STAMINA_MAX = 125

#移動速度の最大最小値
SPEED_MIN = 1
SPEED_MAX = 3

#餌を感知できる範囲
RANGE_FOOD_DETECTION_MIN = 40
RANGE_FOOD_DETECTION_MAX = 75

#繁殖距離とクールダウン
REPRODUCTION_DISTANCE = 5
REPRODUCTION_COOLDOWN = 30


class Organism:
    def __init__(self, org_id, width, height, gender, initial_genes=None, drive_genotype=("W","W")):
        self.org_id = org_id
        self.width = width
        self.height = height
        self.gender = gender
        self.direction = random.uniform(
            np.radians(RANGE_OF_DIRECTIONS[0]),
            np.radians(RANGE_OF_DIRECTIONS[1])
        )
        self.drive_genotype = drive_genotype #遺伝子ドライブの保持
        #個体の初期位置をランダムに設定
        self.position = np.array([random.uniform(0, width), random.uniform(0, height)])
        if initial_genes is None:
            #体力遺伝子の生成と移動速度遺伝子と餌感知範囲遺伝子を生成するところ
            self.genes = {"stamina": random.uniform(STAMINA_MIN, STAMINA_MAX),
                        "detection_range": random.uniform(RANGE_FOOD_DETECTION_MIN, RANGE_FOOD_DETECTION_MAX),
                        "speed": random.uniform(SPEED_MIN, SPEED_MAX)}
        else:
            self.genes = dict(initial_genes)  # 遺伝子をコピーして保持
        self.stamina = self.genes["stamina"]
        self.detection_range = self.genes["detection_range"]
        self.speed = self.genes["speed"]
        self.reproduction_cooldown = 0  # 繁殖クールダウン初期化
        self.birth_frame = None
        #個体の速度ベクトルを計算
        self.velocity = np.array([np.cos(self.direction), np.sin(self.direction)]) * self.speed
        
        self.polygon = np.array([(20, 0), (0, 5), (0, -5)])
        self.type_id = self.org_id % 2
        self.color = ORGANISM_COLORS[self.type_id]

    def update_reproduction_cooldown(self):
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1


    def _clip_gene(self, value, min_value, max_value):
        return max(min_value, min(max_value, value))
    
    def reproduce(self, child_id, width, height, gender, partner, current_frame, a_drive, b_drive):
        # 親からの遺伝子を算術交叉で計算して子の遺伝子とする(突然変異で±10%の範囲で変化、確率は5%)
        p = 0.05 # 突然変異の確率
        constant = 0.5 # 親からの遺伝子割合
        child_genes = {
            "stamina": self.genes["stamina"] * constant + partner.genes["stamina"] * (1 - constant),
            "detection_range": self.genes["detection_range"] * constant + partner.genes["detection_range"] * (1 -constant),
            "speed": self.genes["speed"] * constant + partner.genes["speed"] * (1 - constant),
        }

        #突然変異の処理
        for gene in child_genes:
            if random.random() < p:
                if random.random() < 0.5:
                    child_genes[gene] *= 1.1
                else:
                    child_genes[gene] *= 0.9

        #保持する遺伝子情報の決定(["W","D"]みたいな)
        type_list = []
        for i in [a_drive, b_drive]:
            if i == ["W","W"]:
                a = "W"
                type_list.append(a)
            elif i == ["D","D"]:
                a = "D"
                type_list.append(a)
            else: # WDまたはDWの場合
                if random.random() < 0.9: # いったんDは90%の確率で子に遺伝
                    a = "D"
                    type_list.append(a)
                else:
                    a = "W"
                    type_list.append(a)

        child = Organism(child_id, width, height, gender, initial_genes=child_genes, drive_genotype=type_list)
        child.birth_frame = current_frame

        # 子の位置を親の中間に設定
        child.position = np.array([
            (self.position[0] + partner.position[0]) / 2,
            (self.position[1] + partner.position[1]) / 2,
        ])
        # 子の向きをランダムに設定
        child.direction = random.uniform(
            np.radians(RANGE_OF_DIRECTIONS[0]),
            np.radians(RANGE_OF_DIRECTIONS[1]),
        )
        # 子の速度ベクトル計算
        child.velocity = np.array([np.cos(child.direction), np.sin(child.direction)]) * child.speed
        return child


    def move(self, food_list):
        self.update_reproduction_cooldown()  # 繁殖クールダウンを更新
        target_food = None
        min_dist = float("inf")
        
        for food in food_list:
            dist = np.linalg.norm(food.position - self.position)
            if dist < min_dist and dist <= self.detection_range:
                min_dist = dist
                target_food = food

        if target_food is not None:
            dx, dy = target_food.position - self.position
            self.direction = np.arctan2(dy, dx)
            self.velocity = np.array([np.cos(self.direction), np.sin(self.direction)]) * self.speed
        else:
            # 時折、ランダムな方向に向きを変える
            if random.random() < 0.04:
                self.direction = random.uniform(
                    np.radians(RANGE_OF_DIRECTIONS[0]),
                    np.radians(RANGE_OF_DIRECTIONS[1])
                )
                self.velocity = np.array([np.cos(self.direction), np.sin(self.direction)]) * self.speed

        self.position += self.velocity

        #画面端にいくと反対側から出てくる処理
        if self.position[0] > self.width or self.position[0] < 0:
            self.position[0] = np.abs(self.position[0] - self.width)
        if self.position[1] > self.height or self.position[1] < 0:
            self.position[1] = np.abs(self.position[1] - self.height)

        #体力消費の処理
        self.stamina -= int(0.7 * (self.speed / SPEED_MIN)) # 移動速度に応じて体力を消費
        if self.stamina <= 0:
            self.stamina = 0
            self.velocity = np.zeros(2)


    def display(self, screen, frame_count):
        rotation_matrix = np.array([[np.cos(self.direction), -np.sin(self.direction)],
									[np.sin(self.direction), np.cos(self.direction)]])
        
        rotated_polygon = np.dot(self.polygon, rotation_matrix.T) + self.position
        color = self.color
        if self.birth_frame is not None and frame_count - self.birth_frame <= 5:
            color = (255, 255, 255)

        pygame.draw.polygon(screen, color, rotated_polygon, 0)