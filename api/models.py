"""
API для управления моделями LLM
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Глобальная ссылка на LLM модуль (будет установлена в main.py)
llm_module = None


def init_modules(llm):
    """Инициализация модуля"""
    global llm_module
    llm_module = llm


@router.get("/api/models")
async def get_models():
    """Получение списка доступных моделей Ollama"""
    try:
        import ollama
        models = ollama.list()
        # Извлекаем имена моделей (models - это ListResponse с атрибутом models)
        model_list = [model.model for model in models.models]
        current_model = llm_module.model_name
        return {
            "status": "success",
            "models": model_list,
            "current_model": current_model
        }
    except Exception as e:
        print(f"Ошибка получения списка моделей: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/set-model")
async def set_model(model_data: dict):
    """Смена активной модели LLM"""
    try:
        model_name = model_data.get("model_name")
        if not model_name:
            raise HTTPException(status_code=400, detail="Не указано имя модели")

        # Меняем модель в LLM модуле
        llm_module.set_model(model_name)

        return {
            "status": "success",
            "message": f"Модель изменена на {model_name}",
            "current_model": model_name
        }
    except Exception as e:
        print(f"Ошибка смены модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))
