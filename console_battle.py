import random
import time
from creatures import Player, Monster

def simulate_battle():
    """
    Симуляция боя между Игроком и Монстром с случайными характеристиками.
    """
    print("⚔️  🎲 ГЕНЕРАЦИЯ СЛУЧАЙНОГО БОЯ... 🎲 ⚔️\n")
    time.sleep(1)

    # Генерация случайных параметров для игрока
    player = Player(
        attack=random.randint(10, 25),
        defense=random.randint(5, 20),
        max_health=random.randint(80, 150),
        damage_range=(random.randint(3, 7), random.randint(8, 15))
    )

    # Генерация случайных параметров для монстра
    monster = Monster(
        attack=random.randint(8, 22),
        defense=random.randint(3, 18),
        max_health=random.randint(60, 130),
        damage_range=(random.randint(2, 6), random.randint(7, 13))
    )

    print("🧙 Создан персонаж:")
    print(player)
    print("\n👹 Создан противник:")
    print(monster)
    print("\n" + "🔥" * 40 + "\n")
    time.sleep(2)

    round_num = 1

    while player.is_alive() and monster.is_alive():
        print(f"=== 🎯 РАУНД {round_num} ===")
        print(f"🧙 Игрок: {player.current_health}/{player.max_health} ❤️  | 🧹 Исцелений осталось: {player.heal_uses_left}")
        print(f"👹 Монстр: {monster.current_health}/{monster.max_health} ❤️")
        print("-" * 50)

        # === АТАКА ИГРОКА ===
        print("👉 Игрок атакует монстра...")
        time.sleep(0.5)
        if player.attack_target(monster):
            print("✅ Успешный удар!")
        else:
            print("❌ Промах! Монстр уклонился!")

        # Проверка, жив ли монстр
        if not monster.is_alive():
            print("\n🏆 Монстр повержен! Игрок одержал победу!")
            break

        print()  # пустая строка
        time.sleep(1)

        # === АТАКА МОНСТРА ===
        print("👹 Монстр контратакует...")
        time.sleep(0.5)
        if monster.attack_target(player):
            print("💥 Игрок получил урон!")
        else:
            print("🛡️ Игрок блокировал атаку!")

        # === ПОПЫТКА ИСЦЕЛЕНИЯ ===
        if player.is_alive() and player.current_health < player.max_health * 0.5 and player.heal_uses_left > 0:
            print("\n💊 Игрок пытается использовать исцеление...")
            time.sleep(1)
            if player.heal():
                healed_amount = int(Player.HEAL_PERCENT * player.max_health)
                print(f"✨ Успешно! Восстановлено ~{healed_amount} HP. Текущее здоровье: {player.current_health}/{player.max_health}")
            else:
                print("❌ Не удалось исцелиться (лимит исчерпан или игрок мертв)")

        print("\n" + "="*60 + "\n")
        round_num += 1
        time.sleep(2)  # пауза между раундами для драматизма

    # === ФИНАЛ ===
    if player.is_alive():
        print("🎉 🏆 ПОБЕДА ИГРОКА! 🎉")
        print(f"Осталось здоровья: {player.current_health}/{player.max_health}")
        print(f"Исцелений использовано: {Player.MAX_HEAL_USES - player.heal_uses_left}")
    else:
        print("💀 ИГРОК ПАЛ В БОЮ... МОНСТР ПОБЕДИЛ 💀")
        print(f"Здоровье монстра: {monster.current_health}/{monster.max_health}")

    print("\n" + "⭐" * 40)

if __name__ == "__main__":
    simulate_battle()