from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_current_user
from app.schemas.item import ItemCreate, ItemRead
from app.storage import create_item, delete_item, get_item, list_items_by_owner, update_item_name

router = APIRouter(prefix="/api/v1/items", tags=["Items"])


@router.post("", response_model=ItemRead)
def create_item_secure(data: ItemCreate, user: dict = Depends(get_current_user)):
    it = create_item(owner_id=user["id"], name=data.name)
    return {"id": it["id"], "name": it["name"]}


@router.get("", response_model=List[ItemRead])
def list_items_secure(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    items = list_items_by_owner(owner_id=user["id"], limit=limit, offset=offset)
    return [{"id": it["id"], "name": it["name"]} for it in items]


@router.get("/{item_id}", response_model=ItemRead)
def get_item_secure(item_id: int, user: dict = Depends(get_current_user)):
    it = get_item(item_id)
    if not it:
        raise HTTPException(status_code=404, detail="item not found")
    if it["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"id": it["id"], "name": it["name"]}


@router.patch("/{item_id}", response_model=ItemRead)
def update_item_secure(item_id: int, data: ItemCreate, user: dict = Depends(get_current_user)):
    it = get_item(item_id)
    if not it:
        raise HTTPException(status_code=404, detail="item not found")
    if it["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="forbidden")
    updated = update_item_name(item_id, data.name)
    return {"id": updated["id"], "name": updated["name"]}


@router.delete("/{item_id}")
def delete_item_secure(item_id: int, user: dict = Depends(get_current_user)):
    it = get_item(item_id)
    if not it:
        raise HTTPException(status_code=404, detail="item not found")
    if it["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="forbidden")
    ok = delete_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="item not found")
    return {"deleted": True}
