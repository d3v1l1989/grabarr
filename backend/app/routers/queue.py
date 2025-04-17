from fastapi import APIRouter

router = APIRouter()

@router.get("/queue")
async def get_queue():
    return {"queue": []}

@router.post("/queue")
async def add_to_queue():
    return {"message": "Item added to queue"}

@router.delete("/queue/{item_id}")
async def remove_from_queue(item_id: int):
    return {"message": f"Item {item_id} removed from queue"} 