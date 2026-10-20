def display_name(player) -> str:
    """Имя и фамилия игрока (first_name + last_name), а не username."""
    full_name = " ".join(
        part.strip() for part in (player.first_name, player.last_name) if part and part.strip()
    )
    if full_name:
        return full_name
    return player.username or f"Игрок {player.tg_id}"
