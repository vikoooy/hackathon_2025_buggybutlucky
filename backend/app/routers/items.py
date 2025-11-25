from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_token_header

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@router.get("/")
async def read_items():
    return fake_items_db


@router.get("/{item_id}")
async def read_item(item_id: str):
    for item in fake_items_db:
        if item["item_name"].lower() == item_id.lower():
            return {"item_id": item_id, "item_name": item["item_name"]}
    raise HTTPException(status_code=404, detail="Item not found")
