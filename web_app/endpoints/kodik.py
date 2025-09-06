from fastapi import APIRouter, Response, HTTPException
import os

router = APIRouter()

@router.get("/kodik.txt")
async def get_kodik_text() -> Response:
    """
    Возвращает текст из файла kodik.txt для подтверждения владения ботом.
    """
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "kodik.txt")

    try:
        with open(file_path, encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return Response(content="⚠️ Файл kodik.txt пуст", status_code=204)
            return Response(content=content, media_type="text/plain")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Файл kodik.txt не найден")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении файла: {error}")
