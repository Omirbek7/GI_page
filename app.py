import random
import time
from flask import Flask, render_template, jsonify
from threading import Thread

app = Flask(__name__)

# Глобальные переменные для состояния игры
game_state = {
    "player": None,
    "enemy": None,
    "difficulty": None,
    "battle_log": [],
    "game_running": False
}

# Класс игрока
class Player:
    def __init__(self):
        self.max_hp = random.randint(8674, 15675) + 4780
        self.hp = self.max_hp
        self.base_dmg = round(random.uniform(106, 358) * (1 + 0.466) + 311 + 741)
        DEF = random.uniform(500, 959)
        self.flat_defense_base = round((DEF / (DEF + 190)) * DEF)
        self.cooldown = 4.2
        self.crit_rate = 0.05 + 0.311
        self.crit_dmg = 0.5 + 0.622
        self.passive_cooldown = 0
        self.combo_counter = 0  # Счётчик комбо для обычных атак
        self.last_elemental = 0  # Время последнего элементального навыка
        self.last_burst = 0  # Время последнего взрыва стихии
        self.elemental_cooldown_duration = 11.7  # Увеличено на 17%
        self.burst_cooldown_duration = 38  # Кулдаун взрыва стихии (сек)

    def get_damage(self, attack_type, current_time):
        """Рассчитывает динамический урон в зависимости от типа атаки"""
        self.combo_counter += 1
        if attack_type == "normal":
            combo_multipliers = [0.765, 0.832, 0.82, 0.82, 1.114]
            bonus = 2 if self.combo_counter in [3, 4] else 0
            multiplier = combo_multipliers[(self.combo_counter - 1) % 5]
            damage = round(self.base_dmg * multiplier + bonus)
            if self.combo_counter == 5:
                self.combo_counter = 0  # Сброс комбо после 5-й атаки
        elif attack_type == "elemental" and current_time >= self.last_elemental + self.elemental_cooldown_duration:
            damage = round(self.base_dmg * (2.31 + 0.466))  # 231% + Пиро бонус 46.6%
            self.last_elemental = current_time
        elif attack_type == "burst" and current_time >= self.last_burst + self.burst_cooldown_duration:
            damage = round(self.base_dmg * (6 + 0.466))  # 600% + Пиро бонус 46.6%
            self.last_burst = current_time
        else:
            damage = 0  # Атака на кулдауне
        return damage

    def get_defense(self):
        """Динамическая защита с вариацией ±20% от базовой"""
        return round(self.flat_defense_base * random.uniform(0.8, 1.2))

    @property
    def defense_percentage(self):
        """Для отображения: процент от max_hp, основанный на базовой защите"""
        return round((self.flat_defense_base / self.max_hp) * 100)

# Класс врага
class Enemy:
    def __init__(self, difficulty, player_max_hp, player_dmg):
        if difficulty == 'easy':
            self.max_hp = round(player_max_hp - 4229)
            self.dmg = round(random.uniform(106, 212) * (1 + 0.09) + 36 + 185)
            self.cooldown = 5.4
            self.crit_rate = 0.05 + 0.06
            self.crit_dmg = 0.5 + 0.119
        elif difficulty == 'medium':
            self.max_hp = round(player_max_hp - 2887)
            self.dmg = round(random.uniform(213, 266) * (1 + 0.231) + 123 + 401)
            self.cooldown = 4.9
            self.crit_rate = 0.05 + 0.154
            self.crit_dmg = 0.5 + 0.308
        elif difficulty == 'hard':
            self.max_hp = round(player_max_hp * 1.05 - 1209)
            self.dmg = round(random.uniform(267, 352) * (1 + 0.348) + 232 + 565)
            self.cooldown = 4.6
            self.crit_rate = 0.05 + 0.232
            self.crit_dmg = 0.5 + 0.464

        self.hp = self.max_hp
        self.base_crit_rate = self.crit_rate
        self.passive_cooldown = 0
        self.crit_buff_end = 0
        self.buff_expired_message_shown = False
        self.base_defense_factor = random.uniform(0.17, 0.28)
        self.enhanced_defense = False

        if difficulty == 'hard':
            self.lunar_rings = 0
            self.activation_chance = 9

    @property
    def current_defense_factor(self):
        return self.base_defense_factor + 0.60 if self.enhanced_defense else self.base_defense_factor

    @property
    def defense_percentage(self):
        return round(self.current_defense_factor * 100)

# Функция атаки
def attack(attacker, defender, attack_type="normal"):
    current_time = time.time()
    base_damage = attacker.get_damage(attack_type, current_time) if isinstance(attacker, Player) else attacker.dmg
    if base_damage == 0:
        return

    is_crit = random.random() < attacker.crit_rate
    damage = round(base_damage * (1 + attacker.crit_dmg)) if is_crit else base_damage

    # Усиление защиты врага (medium)
    if isinstance(defender, Enemy) and game_state["difficulty"] == 'medium':
        if defender.hp <= defender.max_hp * 0.52 and not defender.enhanced_defense:
            defender.enhanced_defense = True
            enhanced_defense_value = defender.defense_percentage
            game_state["battle_log"].append(f"Защита врага усилена до {enhanced_defense_value}%!")

    # Защита игрока
    if isinstance(defender, Player):
        defense = defender.get_defense()
        damage_reduced = max(random.randint(105, 278), round(max(0, damage - defense)))
        game_state["battle_log"].append(
            f"Защита игрока снизила урон на {defense} "
            f"({defender.defense_percentage}% от максимального HP)"
        )
    else:
        defense_factor = defender.current_defense_factor
        damage_reduced = max(random.randint(105, 278), round(damage * (1 - defense_factor)))

    defender.hp -= damage_reduced
    game_state["battle_log"].append(
        f"{'Игрок' if isinstance(attacker, Player) else 'Враг'} "
        f"наносит {'критический ' if is_crit else ''}удар: {damage_reduced} урона."
    )

    if defender.hp < 0:
        defender.hp = 0

# Основной цикл боя
def battle_loop():
    global player, enemy
    start_time = time.time()
    next_player_attack = start_time + player.cooldown
    next_enemy_attack = start_time + enemy.cooldown
    next_player_passive = start_time + 4.5
    next_enemy_passive = start_time + (3.5 if game_state["difficulty"] in ['easy', 'hard'] else 2)
    next_elemental = start_time + player.elemental_cooldown_duration
    next_burst = start_time + player.burst_cooldown_duration

    if game_state["difficulty"] == 'easy':
        next_enemy_elemental = start_time + 1.325
    elif game_state["difficulty"] == 'medium':
        next_enemy_elemental = start_time + 3.2
    elif game_state["difficulty"] == 'hard':
        next_enemy_elemental = start_time + 1.8

    while player.hp > 0 and enemy.hp > 0 and game_state["game_running"]:
        current_time = time.time()

        # Пассивка игрока
        if current_time >= next_player_passive:
            hp_loss = round(player.max_hp * 0.045)
            passive_dmg = max(218, round(enemy.hp * 0.163))
            player.hp -= hp_loss
            enemy.hp -= passive_dmg
            game_state["battle_log"].append(
                f"Пассивка игрока: теряет {hp_loss} HP, наносит {passive_dmg} урона."
            )
            next_player_passive = current_time + 4.5

        # Пассивка врага — (easy / medium / hard)
        if current_time >= next_enemy_passive:
            if game_state["difficulty"] == 'easy':
                hp_regen = round(enemy.max_hp * 0.087 - random.randint(194, 357))
                enemy.hp = min(enemy.max_hp, enemy.hp + hp_regen)
                game_state["battle_log"].append(f"Пассивка врага: восстанавливает {hp_regen} HP.")

            elif game_state["difficulty"] == 'medium':
                passive_dmg = round(enemy.max_hp * 0.023 + 25)
                player.hp -= passive_dmg
                game_state["battle_log"].append(f"Пассивка врага: наносит {passive_dmg} урона.")

            elif game_state["difficulty"] == 'hard':
                enemy.crit_rate = enemy.base_crit_rate + 0.11
                enemy.crit_buff_end = current_time + 10
                enemy.buff_expired_message_shown = False
                game_state["battle_log"].append(
                    f"Пассивка врага: шанс крита увеличен до {round(enemy.crit_rate*100)}%."
                )

            next_enemy_passive = current_time + (3.5 if game_state["difficulty"] in ['easy', 'hard'] else 2)

        # Сброс баффа крита (hard)
        if (
            game_state["difficulty"] == 'hard'
            and current_time >= enemy.crit_buff_end
            and not enemy.buff_expired_message_shown
        ):
            enemy.crit_rate = enemy.base_crit_rate
            game_state["battle_log"].append(
                f"Бафф крита врага закончился: шанс крита {round(enemy.crit_rate*100)}%."
            )
            enemy.buff_expired_message_shown = True

        # Элементальный навык врага — easy/medium/hard
        if game_state["difficulty"] == 'easy' and current_time >= next_enemy_elemental:
            dmg = round((enemy.dmg * enemy.dmg) / 210 + random.randint(54, 128))
            player.hp -= round(dmg * (random.randint(77, 89)/100))
            heal = round(enemy.max_hp / enemy.dmg) + 230
            enemy.hp = min(enemy.max_hp, enemy.hp + heal)
            game_state["battle_log"].append(
                f"Элементальный навык врага: Вампирский укус наносит {dmg} урона, восстанавливает {heal} HP."
            )
            next_enemy_elemental = current_time + 1.9875

        elif game_state["difficulty"] == 'medium' and current_time >= next_enemy_elemental:
            enemy.crit_rate = min(1.0, enemy.crit_rate + 0.08)
            enemy.crit_dmg += 0.15
            game_state["battle_log"].append(
                f"Элементалка врага: +8% крит шанса, +15% крит урона "
                f"(теперь {round(enemy.crit_rate*100)}% / {round(enemy.crit_dmg*100)}%)."
            )
            next_enemy_elemental = current_time + 3.2

        elif game_state["difficulty"] == 'hard' and current_time >= next_enemy_elemental:
            enemy.lunar_rings = min(12, enemy.lunar_rings + 2)
            enemy.activation_chance = min(100, enemy.activation_chance + 10)
            game_state["battle_log"].append(
                f"Элементалка врага: +2 кольца (всего {enemy.lunar_rings}), шанс {enemy.activation_chance}%."
            )

            if random.random() * 100 < enemy.activation_chance:
                total = 0
                for _ in range(enemy.lunar_rings):
                    total += round(enemy.dmg * 0.21 + random.randint(125, 299))

                player.hp -= total
                heal = round(total * 0.23 + random.randint(98, 302))
                enemy.hp = min(enemy.max_hp, enemy.hp + heal)

                game_state["battle_log"].append(
                    f"Активация колец: урон {total}, лечение {heal}."
                )

                enemy.lunar_rings = 0
                enemy.activation_chance = 9

            next_enemy_elemental = current_time + 1.8

        # Атака игрока
        if current_time >= next_player_attack:
            attack(player, enemy, "normal")
            next_player_attack = current_time + player.cooldown

        if current_time >= next_elemental:
            attack(player, enemy, "elemental")
            next_elemental = current_time + player.elemental_cooldown_duration

        if current_time >= next_burst:
            attack(player, enemy, "burst")
            next_burst = current_time + player.burst_cooldown_duration

        # Атака врага
        if current_time >= next_enemy_attack:
            attack(enemy, player)
            next_enemy_attack = current_time + enemy.cooldown

        # Завершение боя
        if player.hp <= 0 and enemy.hp <= 0:
            game_state["battle_log"].append("Ничья! Оба бойца погибли.")
            game_state["game_running"] = False
            break
        elif enemy.hp <= 0:
            game_state["battle_log"].append("Вы победили!")
            game_state["game_running"] = False
            break
        elif player.hp <= 0:
            game_state["battle_log"].append("Вы проиграли.")
            game_state["game_running"] = False
            break

        time.sleep(0.01)

# Главная страница
@app.route('/')
def index():
    return render_template('monopoly.html')

# API: состояние игры
@app.route('/game_state')
def get_game_state():
    if game_state["player"] and game_state["enemy"]:
        player = game_state["player"]
        enemy = game_state["enemy"]
    else:
        player = None
        enemy = None

    return jsonify({
        "player_hp": player.hp if player else 0,
        "player_max_hp": player.max_hp if player else 0,
        "player_dmg": player.base_dmg if player else 0,
        "player_defense": player.defense_percentage if player else 0,
        "enemy_hp": enemy.hp if enemy else 0,
        "enemy_max_hp": enemy.max_hp if enemy else 0,
        "enemy_dmg": enemy.dmg if enemy else 0,
        "enemy_defense": enemy.defense_percentage if enemy else 0,
        "battle_log": game_state["battle_log"],
        "game_running": game_state["game_running"]
    })

# API: старт игры
@app.route('/start/<difficulty>')
def start_game(difficulty):
    global player, enemy
    game_state["difficulty"] = difficulty
    game_state["battle_log"] = []
    game_state["game_running"] = True
    player = Player()
    enemy = Enemy(difficulty, player.max_hp, player.base_dmg)
    game_state["player"] = player
    game_state["enemy"] = enemy
    Thread(target=battle_loop).start()
    return jsonify({"status": "Game started"})

if __name__ == '__main__':
    app.run(debug=True)

