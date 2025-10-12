import time
from typing import Dict, List, Optional

# === USERS ===
_next_user_id = 1
USERS: Dict[int, dict] = {}
USERS_BY_USERNAME: Dict[str, int] = {}


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


# === ITEMS (демо для тестов курса) ===
_next_item_id = 1
ITEMS: List[dict] = []  # {"id": int, "name": str, "owner_id": int}


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


# === QUIZZES / QUESTIONS / CHOICES ===
_next_quiz_id = 1
_next_question_id = 1
_next_choice_id = 1

QUIZZES: List[dict] = []  # {"id", "title", "owner_id"}
QUESTIONS: List[dict] = []  # {"id", "quiz_id", "text", "type"}
CHOICES: List[dict] = []  # {"id", "question_id", "text", "is_correct"}


# --- Quiz ---
def create_quiz(owner_id: int, title: str) -> dict:
    global _next_quiz_id
    qid = _next_quiz_id
    _next_quiz_id += 1
    quiz = {"id": qid, "title": title, "owner_id": owner_id}
    QUIZZES.append(quiz)
    return quiz


def get_quiz(quiz_id: int) -> Optional[dict]:
    return next((q for q in QUIZZES if q["id"] == quiz_id), None)


def list_quizzes_by_owner(owner_id: int, limit: int, offset: int) -> List[dict]:
    owned = [q for q in QUIZZES if q["owner_id"] == owner_id]
    return owned[offset : offset + limit]


def update_quiz_title(quiz_id: int, title: str) -> Optional[dict]:
    q = get_quiz(quiz_id)
    if not q:
        return None
    q["title"] = title
    return q


def delete_quiz(quiz_id: int) -> bool:
    # каскадно удаляем вопросы и варианты
    to_delete_q = [qq["id"] for qq in QUESTIONS if qq["quiz_id"] == quiz_id]
    for qid in to_delete_q:
        delete_question(qid)
    for i, q in enumerate(QUIZZES):
        if q["id"] == quiz_id:
            del QUIZZES[i]
            return True
    return False


# --- Question ---
def create_question(quiz_id: int, text: str, qtype: str) -> dict:
    global _next_question_id
    qnid = _next_question_id
    _next_question_id += 1
    question = {"id": qnid, "quiz_id": quiz_id, "text": text, "type": qtype}
    QUESTIONS.append(question)
    return question


def get_question(question_id: int) -> Optional[dict]:
    return next((q for q in QUESTIONS if q["id"] == question_id), None)


def list_questions_by_quiz(quiz_id: int) -> List[dict]:
    return [q for q in QUESTIONS if q["quiz_id"] == quiz_id]


def update_question(
    question_id: int, *, text: Optional[str] = None, qtype: Optional[str] = None
) -> Optional[dict]:
    q = get_question(question_id)
    if not q:
        return None
    if text is not None:
        q["text"] = text
    if qtype is not None:
        q["type"] = qtype
    return q


def delete_question(question_id: int) -> bool:
    # удалить все choices вопроса
    delete_choices_for_question(question_id)
    for i, q in enumerate(QUESTIONS):
        if q["id"] == question_id:
            del QUESTIONS[i]
            return True
    return False


# --- Choice ---
def create_choice(question_id: int, text: str, is_correct: bool) -> dict:
    global _next_choice_id
    cid = _next_choice_id
    _next_choice_id += 1
    choice = {"id": cid, "question_id": question_id, "text": text, "is_correct": is_correct}
    CHOICES.append(choice)
    return choice


def list_choices_by_question(question_id: int) -> List[dict]:
    return [c for c in CHOICES if c["question_id"] == question_id]


def delete_choices_for_question(question_id: int) -> None:
    global CHOICES
    CHOICES = [c for c in CHOICES if c["question_id"] != question_id]


# === RESULTS (in-memory) ===
_next_result_id = 1
RESULTS: List[dict] = []  # {"id","quiz_id","user_id","score","max_score","answers","created_at"}


def save_result(
    quiz_id: int,
    user_id: Optional[int],
    score: int,
    max_score: int,
    answers: list,
) -> dict:
    global _next_result_id
    rid = _next_result_id
    _next_result_id += 1
    rec = {
        "id": rid,
        "quiz_id": quiz_id,
        "user_id": user_id,
        "score": score,
        "max_score": max_score,
        "answers": answers,
        "created_at": int(time.time()),
    }
    RESULTS.append(rec)
    return rec


def list_results_for_quiz(quiz_id: int, user_id: Optional[int] = None) -> List[dict]:
    rows = [r for r in RESULTS if r["quiz_id"] == quiz_id]
    if user_id is not None:
        rows = [r for r in rows if r["user_id"] == user_id]
    # последние сверху
    return sorted(rows, key=lambda r: r["created_at"], reverse=True)
