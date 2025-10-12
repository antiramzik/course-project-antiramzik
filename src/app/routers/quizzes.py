from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_current_user
from app.schemas.quiz import (
    ChoiceCreate,
    ChoicePublic,
    ChoiceRead,
    QuestionCreate,
    QuestionPublic,
    QuestionRead,
    QuestionType,
    QuestionUpdate,
    QuizCreate,
    QuizDetail,
    QuizPreview,
    QuizRead,
    QuizUpdate,
    ResultRead,
    SubmitRequest,
    SubmitResult,
)
from app.storage import (
    create_choice,
    create_question,
    create_quiz,
    delete_choices_for_question,
    delete_question,
    delete_quiz,
    get_question,
    get_quiz,
    list_choices_by_question,
    list_questions_by_quiz,
    list_quizzes_by_owner,
    list_results_for_quiz,
    save_result,
    update_question,
    update_quiz_title,
)

router = APIRouter(prefix="/api/v1", tags=["Quizzes"])


# ---------- helpers ----------
def _ensure_quiz_owner(quiz_id: int, user: dict) -> dict:
    quiz = get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz not found")
    if quiz["owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return quiz


def _ensure_question_owner(question_id: int, user: dict) -> dict:
    q = get_question(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="question not found")
    quiz = get_quiz(q["quiz_id"])
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz not found")
    if quiz["owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return q


def _validate_choices_for_type(qtype: QuestionType, choices: Optional[List[ChoiceCreate]]) -> None:
    if qtype == QuestionType.text:
        if choices and len(choices) > 0:
            raise HTTPException(status_code=400, detail="text question must not have choices")
        return
    if not choices or len(choices) < 2:
        raise HTTPException(status_code=400, detail="variants required (at least 2)")
    correct_count = sum(1 for c in choices if c.is_correct)
    if qtype == QuestionType.single and correct_count != 1:
        raise HTTPException(status_code=400, detail="single must have exactly one correct choice")
    if qtype == QuestionType.multiple and correct_count < 1:
        raise HTTPException(
            status_code=400, detail="multiple must have at least one correct choice"
        )


def _read_question(question_id: int) -> QuestionRead:
    q = get_question(question_id)
    choices = list_choices_by_question(question_id)
    return QuestionRead(
        id=q["id"],
        text=q["text"],
        type=QuestionType(q["type"]),
        choices=[ChoiceRead(id=c["id"], text=c["text"]) for c in choices] if choices else None,
    )


def _public_question(question_id: int) -> QuestionPublic:
    q = get_question(question_id)
    choices = list_choices_by_question(question_id)
    return QuestionPublic(
        id=q["id"],
        text=q["text"],
        type=QuestionType(q["type"]),
        choices=[ChoicePublic(text=c["text"]) for c in choices] if choices else None,
    )


def _grade(quiz_id: int, payload: SubmitRequest) -> SubmitResult:
    questions = list_questions_by_quiz(quiz_id)
    qmap = {q["id"]: q for q in questions}
    max_score = sum(1 for q in questions if q["type"] in ("single", "multiple"))
    choices_by_q = {q["id"]: list_choices_by_question(q["id"]) for q in questions}

    score = 0
    for ans in payload.answers:
        q = qmap.get(ans.question_id)
        if not q:
            continue
        qtype = q["type"]
        if qtype == "single" and ans.choice_id is not None:
            target = next((c for c in choices_by_q[q["id"]] if c["id"] == ans.choice_id), None)
            if target and target["is_correct"]:
                score += 1
        elif qtype == "multiple" and ans.choice_ids:
            correct_ids = sorted([c["id"] for c in choices_by_q[q["id"]] if c["is_correct"]])
            given = sorted(list(set(ans.choice_ids)))
            if given == correct_ids:
                score += 1
        # text — не автооцениваем
    return SubmitResult(score=score, max_score=max_score)


# ---------- Quizzes ----------
@router.post("/quizzes", response_model=QuizRead)
def create_quiz_endpoint(data: QuizCreate, user: dict = Depends(get_current_user)):
    quiz = create_quiz(owner_id=user["id"], title=data.title)
    return QuizRead(id=quiz["id"], title=quiz["title"])


@router.get("/quizzes", response_model=List[QuizRead])
def list_quizzes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    qs = list_quizzes_by_owner(user["id"], limit, offset)
    return [QuizRead(id=q["id"], title=q["title"]) for q in qs]


@router.get("/quizzes/{quiz_id}", response_model=QuizDetail)
def get_quiz_detail(quiz_id: int, user: dict = Depends(get_current_user)):
    quiz = _ensure_quiz_owner(quiz_id, user)
    questions = list_questions_by_quiz(quiz_id)
    return QuizDetail(
        id=quiz["id"], title=quiz["title"], questions=[_read_question(q["id"]) for q in questions]
    )


@router.patch("/quizzes/{quiz_id}", response_model=QuizRead)
def update_quiz_endpoint(quiz_id: int, data: QuizUpdate, user: dict = Depends(get_current_user)):
    _ensure_quiz_owner(quiz_id, user)
    q = update_quiz_title(quiz_id, data.title) if data.title else get_quiz(quiz_id)
    if not q:
        raise HTTPException(status_code=404, detail="quiz not found")
    return QuizRead(id=q["id"], title=q["title"])


@router.delete("/quizzes/{quiz_id}")
def delete_quiz_endpoint(quiz_id: int, user: dict = Depends(get_current_user)):
    _ensure_quiz_owner(quiz_id, user)
    ok = delete_quiz(quiz_id)
    if not ok:
        raise HTTPException(status_code=404, detail="quiz not found")
    return {"deleted": True}


# ---------- Questions ----------
@router.post("/questions", response_model=QuestionRead)
def create_question_endpoint(data: QuestionCreate, user: dict = Depends(get_current_user)):
    _ensure_quiz_owner(data.quiz_id, user)
    _validate_choices_for_type(data.type, data.choices)

    q = create_question(quiz_id=data.quiz_id, text=data.text, qtype=data.type.value)
    if data.type != QuestionType.text and data.choices:
        for c in data.choices:
            create_choice(question_id=q["id"], text=c.text, is_correct=c.is_correct)

    return _read_question(q["id"])


@router.get("/questions", response_model=List[QuestionRead])
def list_questions(quiz_id: int, user: dict = Depends(get_current_user)):
    _ensure_quiz_owner(quiz_id, user)
    qs = list_questions_by_quiz(quiz_id)
    return [_read_question(q["id"]) for q in qs]


@router.get("/questions/{question_id}", response_model=QuestionRead)
def get_question_endpoint(question_id: int, user: dict = Depends(get_current_user)):
    _ensure_question_owner(question_id, user)
    return _read_question(question_id)


@router.patch("/questions/{question_id}", response_model=QuestionRead)
def update_question_endpoint(
    question_id: int, data: QuestionUpdate, user: dict = Depends(get_current_user)
):
    q = _ensure_question_owner(question_id, user)
    current_type = QuestionType(q["type"])
    new_type = data.type or current_type

    if data.choices is not None:
        _validate_choices_for_type(new_type, data.choices)

    updated = update_question(
        question_id,
        text=data.text if data.text is not None else None,
        qtype=new_type.value if data.type is not None else None,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="question not found")

    if data.choices is not None:
        delete_choices_for_question(question_id)
        if new_type != QuestionType.text:
            for c in data.choices:
                create_choice(question_id=question_id, text=c.text, is_correct=c.is_correct)

    if data.type == QuestionType.text and data.choices is None:
        delete_choices_for_question(question_id)

    return _read_question(question_id)


@router.delete("/questions/{question_id}")
def delete_question_endpoint(question_id: int, user: dict = Depends(get_current_user)):
    _ensure_question_owner(question_id, user)
    ok = delete_question(question_id)
    if not ok:
        raise HTTPException(status_code=404, detail="question not found")
    return {"deleted": True}


# ---------- Preview (owner) ----------
@router.get("/quizzes/{quiz_id}/preview", response_model=QuizPreview)
def preview_quiz(quiz_id: int, user: dict = Depends(get_current_user)):
    quiz = _ensure_quiz_owner(quiz_id, user)
    questions = list_questions_by_quiz(quiz_id)
    return QuizPreview(
        id=quiz["id"], title=quiz["title"], questions=[_public_question(q["id"]) for q in questions]
    )


# ---------- Submit (owner) ----------
@router.post("/quizzes/{quiz_id}/submit", response_model=SubmitResult)
def submit_quiz(quiz_id: int, payload: SubmitRequest, user: dict = Depends(get_current_user)):
    _ensure_quiz_owner(quiz_id, user)
    result = _grade(quiz_id, payload)
    save_result(
        quiz_id=quiz_id,
        user_id=user["id"],
        score=result.score,
        max_score=result.max_score,
        answers=[a.dict() for a in payload.answers],
    )
    return result


# ---------- PUBLIC endpoints (без авторизации) ----------
@router.get("/public/quizzes/{quiz_id}/preview", response_model=QuizPreview)
def public_preview(quiz_id: int):
    quiz = get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz not found")
    questions = list_questions_by_quiz(quiz_id)
    return QuizPreview(
        id=quiz["id"], title=quiz["title"], questions=[_public_question(q["id"]) for q in questions]
    )


@router.post("/public/quizzes/{quiz_id}/submit", response_model=SubmitResult)
def public_submit(quiz_id: int, payload: SubmitRequest):
    quiz = get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz not found")
    result = _grade(quiz_id, payload)
    save_result(
        quiz_id=quiz_id,
        user_id=None,
        score=result.score,
        max_score=result.max_score,
        answers=[a.dict() for a in payload.answers],
    )
    return result


# ---------- Results (история) ----------
@router.get("/quizzes/{quiz_id}/results", response_model=List[ResultRead])
def results_for_quiz(quiz_id: int, user: dict = Depends(get_current_user)):
    _ensure_quiz_owner(quiz_id, user)
    rows = list_results_for_quiz(quiz_id)
    return [
        ResultRead(
            id=r["id"],
            user_id=r["user_id"],
            score=r["score"],
            max_score=r["max_score"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/quizzes/{quiz_id}/my-results", response_model=List[ResultRead])
def my_results(quiz_id: int, user: dict = Depends(get_current_user)):
    _ensure_quiz_owner(
        quiz_id, user
    )  # можно убрать, если хочешь, чтобы студент видел свои результаты даже в чужом квизе
    rows = list_results_for_quiz(quiz_id, user_id=user["id"])
    return [
        ResultRead(
            id=r["id"],
            user_id=r["user_id"],
            score=r["score"],
            max_score=r["max_score"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
