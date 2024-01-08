from fastapi import APIRouter, status
from fastapi import Request
from fastapi.responses import JSONResponse
from app.api.sns.sns_handler import handle

###############################################################################

router = APIRouter(
    prefix="/sns",
    tags=["sns"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

###############################################################################

@router.post("/notify")
async def handle_sns_notification(message: Request):
    try:
        print("Notification received")
        result = await handle(message)
        return JSONResponse(content=result)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Internal Server Error"})
