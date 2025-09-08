# bot/dungeon.py
import random

class Room:
    def __init__(self, x: int, y: int, room_type: str = "empty"):
        self.x = x
        self.y = y
        self.room_type = room_type  # "empty", "monster", "treasure", "trap", "start", "exit"
        self.visited = False

class Dungeon:
    def __init__(self, width: int = 5, height: int = 5):
        self.width = width
        self.height = height
        self.rooms = {}
        self.player_x = 0
        self.player_y = 0
        self.generate_dungeon()

    def generate_dungeon(self):
        # Создаём сетку комнат
        for x in range(self.width):
            for y in range(self.height):
                room_type = "empty"
                # Начальная комната
                if x == 0 and y == 0:
                    room_type = "start"
                # Сокровищница — в противоположном углу
                elif x == self.width - 1 and y == self.height - 1:
                    room_type = "exit"
                else:
                    # Случайно распределяем монстров, ловушки, сокровища
                    rand = random.random()
                    if rand < 0.4:
                        room_type = "monster"
                    elif rand < 0.6:
                        room_type = "treasure"
                    elif rand < 0.7:
                        room_type = "trap"

                self.rooms[(x, y)] = Room(x, y, room_type)

    def get_current_room(self) -> Room:
        return self.rooms.get((self.player_x, self.player_y))

    def move_player(self, direction: str) -> bool:
        """Перемещает игрока. Возвращает True, если перемещение успешно."""
        dx, dy = 0, 0
        if direction == "up" and self.player_y > 0:
            dy = -1
        elif direction == "down" and self.player_y < self.height - 1:
            dy = 1
        elif direction == "left" and self.player_x > 0:
            dx = -1
        elif direction == "right" and self.player_x < self.width - 1:
            dx = 1
        else:
            return False  # Невозможно двигаться в этом направлении

        self.player_x += dx
        self.player_y += dy
        return True

    def get_available_directions(self) -> list[str]:
        """Возвращает список доступных направлений для движения."""
        directions = []
        if self.player_y > 0:
            directions.append("⬆️ Вверх")
        if self.player_y < self.height - 1:
            directions.append("⬇️ Вниз")
        if self.player_x > 0:
            directions.append("⬅️ Налево")
        if self.player_x < self.width - 1:
            directions.append("➡️ Направо")
        return directions

    def render_map(self) -> str:
        """Возвращает текстовую карту подземелья."""
        lines = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if x == self.player_x and y == self.player_y:
                    row.append("🧙")  # Игрок
                elif self.rooms[(x, y)].visited:
                    room = self.rooms[(x, y)]
                    if room.room_type == "monster":
                        row.append("👹")
                    elif room.room_type == "treasure":
                        row.append("💰")
                    elif room.room_type == "trap":
                        row.append("💀")
                    elif room.room_type == "exit":
                        row.append("🏆")
                    else:
                        row.append("⬜")
                else:
                    row.append("⬛")  # Неизведанная комната
            lines.append("".join(row))
        return "\n".join(lines)