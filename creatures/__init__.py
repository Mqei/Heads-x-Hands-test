from creatures.monster import Monster
from creatures.player import Player


player = Player(attack=15, defense=10, max_health=100, damage_range=(5, 10))
monster = Monster(attack=12, defense=8, max_health=60, damage_range=(3, 8))

print("Игрок атакует монстра...")
if player.attack_target(monster):
    print("Попадание!")
else:
    print("Промах!")

print(f"Здоровье монстра: {monster.current_health}")

if monster.is_alive():
    print("Монстр атакует...")
    monster.attack_target(player)

print(f"Здоровье игрока: {player.current_health}")

player.heal()
print(f"Игрок исцелился. Здоровье: {player.current_health}")