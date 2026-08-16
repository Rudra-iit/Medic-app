def normalize_role(role: str | None) -> str:
    """Normalize role values so role checks are case-insensitive and whitespace-safe."""
    if not role:
        return "client"

    normalized = str(role).strip().lower()
    if normalized in {"admin", "staff", "client"}:
        return normalized

    return "client"
