import random
import time
from flask import Flask, render_template, jsonify
from threading import Thread

app = Flask(__name__)

game_state = {
    "player": None,
    "enemy": None,
    "difficulty": None,
    "battle_log": [],
    "game_running": False
}

# База данных для оружия
WEAPONS = [
    # 1* оружие
    {'rarity': '1*', 'base_stat': 185, 'sub_stat': {}, 'passive_talent': {}},
    # 2* оружие
    {'rarity': '2*', 'base_stat': 243, 'sub_stat': {}, 'passive_talent': {}},
    # 3* оружие, 1-й тип
    {'rarity': '3*', 'base_stat': 401, 'sub_stat': {'hp_percent': 0.352}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 401, 'sub_stat': {'dmg_percent': 0.352}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 401, 'sub_stat': {'crit_dmg': 0.469}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 401, 'sub_stat': {'def_percent': 0.0439}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 401, 'sub_stat': {'phys_dmg_bonus': 0.432}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 401, 'sub_stat': {'crit_rate': 0.234}, 'passive_talent': {}},
    # 3* оружие, 2-й тип
    {'rarity': '3*', 'base_stat': 448, 'sub_stat': {'dmg_percent': 0.234}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 448, 'sub_stat': {'def_percent': 0.0275}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 448, 'sub_stat': {'crit_dmg': 0.312}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 448, 'sub_stat': {'crit_rate': 0.156}, 'passive_talent': {}},
    # 3* оружие, 3-й тип
    {'rarity': '3*', 'base_stat': 354, 'sub_stat': {'hp_percent': 0.469}, 'passive_talent': {}},
    {'rarity': '3*', 'base_stat': 354, 'sub_stat': {'crit_rate': 0.312}, 'passive_talent': {}},
    # 4* , 1-
    {'rarity': '4*', 'base_stat': 510, 'sub_stat': {'hp_percent': 0.413}, 'passive_talent': {}},
    {'rarity': '4*', 'base_stat': 510, 'sub_stat': {'dmg_percent': 0.413}, 'passive_talent': {}},
    {'rarity': '4*', 'base_stat': 510, 'sub_stat': {'crit_rate': 0.276}, 'passive_talent': {}},
    {'rarity': '4*', 'base_stat': 510, 'sub_stat': {'crit_dmg': 0.551}, 'passive_talent': {}},
    {'rarity': '4*', 'base_stat': 510, 'sub_stat': {'def_percent': 0.0517}, 'passive_talent': {}},
    {'rarity': '4*', 'base_stat': 510, 'sub_stat': {'phys_dmg_bonus': 0.517}, 'passive_talent': {}},
    # 5* оружие (пример)
    {
        'rarity': '5*',
        'base_stat': 741,
        'sub_stat': {'crit_rate': 0.11},  # 11% Crit Rate
        'passive_talent': {
            'effect': 'after_elemental_dmg_boost',
            'dmg_bonus': 0.15,  # +15% урона
            'duration': 6       # 6 секунд
        }
    }
]

# Класс игрока
class Player:
    def __init__(self):
        self.max_hp = 10000
        self.hp = self.max_hp
        self.weapon = random.choice([w for w in WEAPONS if w['rarity'] == '3*'])  # Пока 3*, можно изменить
        self.base_dmg = self.weapon['base_stat']
        self.sub_stat = self.weapon['sub_stat']
        self.passive_talent = self.weapon['passive_talent']
        self.cooldown = 4.0
        self.passive_active_until = 0  # Время окончания действия пассивки
        self.elemental_skill_last_used = 0  # Время последнего использования элементального навыка
        self.elemental_cooldown = 10.0  # Кулдаун элементального навыка

    def get_defense_percentage(self):
        return 0

    def calculate_damage(self, attack_type="normal"):
        damage = self.base_dmg
        # Учитываем подстаты
        if 'dmg_percent' in self.sub_stat:
            damage += self.base_dmg * self.sub_stat['dmg_percent']
        if 'phys_dmg_bonus' in self.sub_stat:
            damage += self.base_dmg * self.sub_stat['phys_dmg_bonus']
        if 'crit_rate' in self.sub_stat and random.random() < self.sub_stat['crit_rate']:
            damage *= 1.5  # Простой критический множитель

        # Учитываем пассивный талант
        current_time = time.time()
        if attack_type == "elemental":
            self.elemental_skill_last_used = current_time
            if self.passive_talent.get('effect') == 'after_elemental_dmg_boost':
                self.passive_active_until = current_time + self.passive_talent['duration']
                game_state["battle_log"].append("Пассивный талант активирован: +15% урона на 6 сек.")

        if current_time <= self.passive_active_until:
            damage *= (1 + self.passive_talent.get('dmg_bonus', 0))

        return round(damage)

# Класс врага
class Enemy:
    def __init__(self, difficulty, player_max_hp, player_dmg):
        if difficulty == 'easy':
            self.max_hp = round(player_max_hp * 0.8)
            self.weapon = random.choice([w for w in WEAPONS if w['rarity'] == '2*'])
            self.cooldown = 6.0
        elif difficulty == 'medium':
            self.max_hp = round(player_max_hp * 0.9)
            self.weapon = random.choice([w for w in WEAPONS if w['rarity'] == '3*'])
            self.cooldown = 5.5
        elif difficulty == 'hard':
            self.max_hp = player_max_hp
            self.weapon = random.choice([w for w in WEAPONS if w['rarity'] == '3*'])
            self.cooldown = 5.0
        else:  # very_hard
            self.max_hp = round(player_max_hp * 1.1)
            self.weapon = random.choice([w for w in WEAPONS if w['rarity'] == '5*'])  # 5* для very_hard
            self.cooldown = 4.5
        self.hp = self.max_hp
        self.base_dmg = self.weapon['base_stat']
        self.sub_stat = self.weapon['sub_stat']
        self.passive_talent = self.weapon['passive_talent']
        self.passive_active_until = 0

    def get_defense_percentage(self):
        return 0

    def calculate_damage(self):
        damage = self.base_dmg
        if 'dmg_percent' in self.sub_stat:
            damage += self.base_dmg * self.sub_stat['dmg_percent']
        if 'phy_dmg_bonus' in self.sub_stat:
            damage += self.base_dmg * self.sub_stat['phys_dmg_bonus']
        if 'crit_rate' in self.sub_stat and random.random() < self.sub_stat['crit_rate']:
            damage *= 1.5

        current_time = time.time()
        if current_time <= self.passive_active_until:
            damage *= (1 + self.passive_talent.get('dmg_bonus', 0))

        return round(damage)

# Функция боя
def battle_loop():
    global game_state
    player = game_state["player"]
    enemy = game_state["enemy"]
    start_time = time.time()
    next_player_attack = start_time + player.cooldown
    next_enemy_attack = start_time + enemy.cooldown
    next_elemental_attack = start_time + player.elemental_cooldown

    while player.hp > 0 and enemy.hp > 0 and game_state["game_running"]:
        current_time = time.time()

        # Обычная атака игрока
        if current_time >= next_player_attack:
            damage = player.calculate_damage("normal")
            enemy.hp -= damage
            game_state["battle_log"].append(f"Игрок наносит {damage} урона врагу.")
            game_state["battle_log"].append(f"HP врага: {enemy.hp}")
            next_player_attack = current_time + player.cooldown

        # Элементальная атака игрока
        if current_time >= next_elemental_attack:
            damage = player.calculate_damage("elemental")
            enemy.hp -= damage
            game_state["battle_log"].append(f"Игрок использует элементальный навык: {damage} урона врагу.")
            game_state["battle_log"].append(f"HP врага: {enemy.hp}")
            next_elemental_attack = current_time + player.elemental_cooldown

        # Атака врага
        if current_time >= next_enemy_attack:
            damage = enemy.calculate_damage()
            player.hp -= damage
            game_state["battle_log"].append(f"Враг наносит {damage} урона игроку.")
            game_state["battle_log"].append(f"Ваш HP: {player.hp}")
            next_enemy_attack = current_time + enemy.cooldown

        if enemy.hp <= 0:
            game_state["battle_log"].append("Вы победили!")
            game_state["game_running"] = False
            break
        if player.hp <= 0:
            game_state["battle_log"].append("Вы проиграли.")
            game_state["game_running"] = False
            break

        time.sleep(0.01)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game_state')
def get_game_state():
    player = game_state["player"]
    enemy = game_state["enemy"]
    return jsonify({
        "player_hp": player.hp if player else 0,
        "player_max_hp": player.max_hp if player else 0,
        "player_dmg": player.base_dmg if player else 0,
        "player_defense": player.get_defense_percentage() if player else 0,
        "enemy_hp": enemy.hp if enemy else 0,
        "enemy_max_hp": enemy.max_hp if enemy else 0,
        "enemy_dmg": enemy.base_dmg if enemy else 0,
        "enemy_defense": enemy.get_defense_percentage() if enemy else 0,
        "battle_log": game_state["battle_log"],
        "game_running": game_state["game_running"]
    })

@app.route('/start/<difficulty>')
def start_game(difficulty):
    global game_state
    game_state["difficulty"] = difficulty
    game_state["battle_log"] = []
    game_state["game_running"] = True
    game_state["player"] = Player()
    game_state["enemy"] = Enemy(difficulty, game_state["player"].max_hp, game_state["player"].base_dmg)
    Thread(target=battle_loop).start()
    return jsonify({"status": "Game started"})

if __name__ == '__main__':
    app.run(debug=True)