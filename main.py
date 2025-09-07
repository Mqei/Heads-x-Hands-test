from creatures import Player, Monster
import time
import random

def simulate_battle():
    print("⚔️  НАЧАЛО БИТВЫ ⚔️\n")

    # Случайные параметры для игрока и монстра
    player = Player(
        attack=random.randint(10, 20),
        defense=random.randint(5, 15),
        max_health=random.randint(80, 120),
        damage_range=(random.randint(3, 6), random.randint(7, 12))
    )

    monster = Monster(
        attack=random.randint(8, 18),
        defense=random.randint(3, 12),
        max_health=random.randint(50, 100),
        damage_range=(random.randint(2, 5), random.randint(6, 10))
    )
def simulate_battle():
    """
    Пример симуляции боя между Игроком и Монстром.
    """
    print("⚔️  НАЧАЛО БИТВЫ ⚔️\n")

    # Создаём игрока и монстра
    player = Player(
        attack=15,
        defense=10,
        max_health=100,
        damage_range=(5, 10)
    )

    monster = Monster(
        attack=12,
        defense=8,
        max_health=60,
        damage_range=(3, 8)
    )

    round_num = 1

    while player.is_alive() and monster.is_alive():
        print(f"=== Раунд {round_num} ===")
        print(player)
        print(monster)
        print("-" * 40)

        # Игрок атакует монстра
        print("👉 Игрок атакует монстра...")
        if player.attack_target(monster):
            print("✅ Попадание! Монстр получил урон.")
        else:
            print("❌ Промах!")

        # Проверяем, выжил ли монстр
        if not monster.is_alive():
            print("🏆 Монстр повержен! Игрок победил!")
            break

        # Монстр атакует игрока
        print("\n👹 Монстр атакует игрока...")
        if monster.attack_target(player):
            print("💥 Попадание! Игрок получил урон.")
        else:
            print("🛡️ Игрок уклонился!")

        # Если игрок ранен, попробуем исцелиться
        if player.is_alive() and player.current_health < player.max_health // 2:
            print("\n💊 Игрок пытается исцелиться...")
            if player.heal():
                print(f"✨ Исцеление успешно! Здоровье: {player.current_health}/{player.max_health}")
            else:
                print("❌ Невозможно исцелиться (либо мертв, либо лимит исчерпан)")

        print("\n" + "="*50 + "\n")
        round_num += 1
        time.sleep(1)  # пауза для удобства чтения

    # Финальный результат
    if player.is_alive():
        print("🎉 ПОБЕДА ИГРОКА!")
    else:
        print("💀 Игрок пал в бою...")

if __name__ == "__main__":
    simulate_battle()