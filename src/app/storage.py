from typing import Dict, List, Optional

_next_user_id = 1
_next_item_id = 1

USERS: Dict[int, dict] = {}
USERS_BY_USERNAME: Dict[str, int] = {}
ITEMS: List[dict] = []  # {"id": int, "name": str, "owner_id": int}


def create_user(username: str, pwd_hash: str, role: str = "user") -> dict:
    global _next_user_id
    if username in USERS_BY_USERNAME:
        raise ValueError("username_taken")
    uid = _next_user_id
    _next_user_id += 1
    user = {"id": uid, "username": username, "password_hash": pwd_hash, "role": role}
    USERS[uid] = user
    USERS_BY_USERNAME[username] = uid
    return user


def get_user_by_username(username: str) -> Optional[dict]:
    uid = USERS_BY_USERNAME.get(username)
    return USERS.get(uid) if uid is not None else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    return USERS.get(user_id)


def create_item(owner_id: int, name: str) -> dict:
    global _next_item_id
    iid = _next_item_id
    _next_item_id += 1
    item = {"id": iid, "name": name, "owner_id": owner_id}
    ITEMS.append(item)
    return item


def get_item(item_id: int) -> Optional[dict]:
    return next((it for it in ITEMS if it["id"] == item_id), None)


def list_items_all(limit: int, offset: int) -> List[dict]:
    return ITEMS[offset : offset + limit]


def list_items_by_owner(owner_id: int, limit: int, offset: int) -> List[dict]:
    owned = [it for it in ITEMS if it["owner_id"] == owner_id]
    return owned[offset : offset + limit]


def update_item_name(item_id: int, new_name: str) -> Optional[dict]:
    it = get_item(item_id)
    if not it:
        return None
    it["name"] = new_name
    return it


def delete_item(item_id: int) -> bool:
    for i, it in enumerate(ITEMS):
        if it["id"] == item_id:
            del ITEMS[i]
            return True
    return False
