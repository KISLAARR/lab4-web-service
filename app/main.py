from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# ========== МОДЕЛЬ ДАННЫХ ==========
class Trip(BaseModel):
    """Модель данных для туристической поездки"""
    id: Optional[str] = None
    destination: str                    # Место назначения (строковое)
    country: str                       # Страна (строковое)
    travel_agency: str                 # Турфирма (строковое)
    duration_days: int                 # Продолжительность в днях (числовое)
    price: float                      # Цена (числовое)
    rating: float                     # Рейтинг (числовое)
    group_size: int                   # Размер группы (числовое)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "destination": "Париж",
                "country": "Франция", 
                "travel_agency": "ТурМир",
                "duration_days": 7,
                "price": 120000.0,
                "rating": 4.8,
                "group_size": 15
            }
        }

# ========== ПРИЛОЖЕНИЕ FASTAPI ==========
app = FastAPI(
    title="API Туристических поездок",
    description="Лабораторная работа №4. Веб-сервис для управления туристическими поездками",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ========== БАЗА ДАННЫХ В ПАМЯТИ ==========
trips_db = []
STATIC_TRIPS = [
    {
        "destination": "Париж",
        "country": "Франция",
        "travel_agency": "ТурМир",
        "duration_days": 7,
        "price": 120000.0,
        "rating": 4.8,
        "group_size": 15
    },
    {
        "destination": "Бали",
        "country": "Индонезия",
        "travel_agency": "АзияТур",
        "duration_days": 10,
        "price": 185000.0,
        "rating": 4.6,
        "group_size": 12
    },
    {
        "destination": "Токио",
        "country": "Япония",
        "travel_agency": "ВостокТур",
        "duration_days": 8,
        "price": 220000.0,
        "rating": 4.9,
        "group_size": 8
    },
    {
        "destination": "Нью-Йорк",
        "country": "США",
        "travel_agency": "АмерикаТур",
        "duration_days": 12,
        "price": 250000.0,
        "rating": 4.7,
        "group_size": 20
    },
    {
        "destination": "Дубай",
        "country": "ОАЭ",
        "travel_agency": "ВостокТур",
        "duration_days": 9,
        "price": 190000.0,
        "rating": 4.5,
        "group_size": 18
    }
]

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_current_time():
    """Возвращает текущее время в строковом формате"""
    return datetime.now().isoformat()

def initialize_database():
    """Инициализация базы данных начальными значениями"""
    global trips_db
    trips_db.clear()
    
    for trip_data in STATIC_TRIPS:
        trip_id = str(uuid.uuid4())
        now = get_current_time()
        trip = Trip(
            **trip_data,
            id=trip_id,
            created_at=now,
            updated_at=now
        )
        trips_db.append(trip)

def find_trip_by_id(trip_id: str) -> Optional[Trip]:
    """Найти поездку по ID"""
    for trip in trips_db:
        if trip.id == trip_id:
            return trip
    return None

def find_trip_index(trip_id: str) -> int:
    """Найти индекс поездки в списке"""
    for i, trip in enumerate(trips_db):
        if trip.id == trip_id:
            return i
    return -1

# ========== ОБРАБОТЧИКИ СОБЫТИЙ ==========
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    initialize_database()
    print(f"✅ Сервис запущен. Загружено {len(trips_db)} поездок.")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении работы"""
    print("⚠️  Сервис останавливается...")

# ========== API ENDPOINTS ==========

# 1. КОРНЕВОЙ ЭНДПОИНТ
@app.get("/", tags=["Информация"])
async def root():
    """Корневой endpoint с информацией о API"""
    return {
        "service": "API Туристических поездок",
        "version": "1.0.0",
        "author": "Студент (Лабораторная работа №4)",
        "endpoints": {
            "get_all_trips": "/trips",
            "get_trip": "/trips/{id}",
            "create_trip": "/trips",
            "update_trip": "/trips/{id}",
            "patch_trip": "/trips/{id}/patch",
            "delete_trip": "/trips/{id}",
            "statistics": "/statistics"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

# 2. ПОЛУЧИТЬ ВСЕ ПОЕЗДКИ (С СОРТИРОВКОЙ)
@app.get("/trips", response_model=List[Trip], tags=["Поездки"])
async def get_all_trips(
    sort_by: Optional[str] = Query(
        None,
        description="Поле для сортировки (destination, country, price, rating, duration_days, group_size)"
    ),
    reverse: bool = Query(
        False,
        description="True - по убыванию, False - по возрастанию"
    )
):
    """
    Получить список всех туристических поездок.
    
    Поддерживает сортировку по любому полю модели.
    """
    result = trips_db.copy()
    
    if sort_by:
        try:
            # Пытаемся отсортировать по указанному полю
            result.sort(
                key=lambda x: getattr(x, sort_by),
                reverse=reverse
            )
        except AttributeError:
            # Если поле не существует, возвращаем без сортировки
            pass
    
    return result

# 3. ПОЛУЧИТЬ ПОЕЗДКУ ПО ID
@app.get("/trips/{trip_id}", response_model=Trip, tags=["Поездки"])
async def get_trip(trip_id: str):
    """Получить информацию о конкретной поездке по её ID"""
    trip = find_trip_by_id(trip_id)
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Поездка с ID '{trip_id}' не найдена"
        )
    
    return trip

# 4. СОЗДАТЬ НОВУЮ ПОЕЗДКУ
@app.post("/trips", 
          response_model=Trip, 
          status_code=status.HTTP_201_CREATED,
          tags=["Поездки"])
async def create_trip(trip: Trip):
    """
    Создать новую туристическую поездку.
    
    ID будет сгенерирован автоматически.
    """
    # Генерируем уникальный ID
    trip_id = str(uuid.uuid4())
    now = get_current_time()
    
    # Устанавливаем служебные поля
    trip.id = trip_id
    trip.created_at = now
    trip.updated_at = now
    
    # Добавляем в базу данных
    trips_db.append(trip)
    
    return trip

# 5. ПОЛНОСТЬЮ ОБНОВИТЬ ПОЕЗДКУ (PUT)
@app.put("/trips/{trip_id}", response_model=Trip, tags=["Поездки"])
async def update_trip(trip_id: str, updated_trip: Trip):
    """
    Полностью обновить информацию о поездке (PUT).
    
    Заменяет все поля поездки на новые значения.
    Требует отправки всех полей модели.
    """
    trip_index = find_trip_index(trip_id)
    
    if trip_index == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Поездка с ID '{trip_id}' не найдена"
        )
    
    # Сохраняем оригинальные даты создания
    original_trip = trips_db[trip_index]
    
    # Обновляем данные
    updated_trip.id = trip_id
    updated_trip.created_at = original_trip.created_at
    updated_trip.updated_at = get_current_time()
    
    # Заменяем в базе данных
    trips_db[trip_index] = updated_trip
    
    return updated_trip

# 6. ЧАСТИЧНО ОБНОВИТЬ ПОЕЗДКУ (PATCH)
@app.patch("/trips/{trip_id}", response_model=Trip, tags=["Поездки"])
async def patch_trip(trip_id: str, trip_update: dict):
    """
    Частично обновить информацию о поездке (PATCH).
    
    Позволяет обновлять только указанные поля.
    Не требует отправки всех полей модели.
    """
    trip_index = find_trip_index(trip_id)
    
    if trip_index == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Поездка с ID '{trip_id}' не найдена"
        )
    
    # Получаем текущую поездку
    current_trip = trips_db[trip_index]
    trip_dict = current_trip.dict()
    
    # Обновляем только указанные поля
    for key, value in trip_update.items():
        if key in trip_dict and key not in ['id', 'created_at']:
            trip_dict[key] = value
    
    # Обновляем дату изменения
    trip_dict['updated_at'] = get_current_time()
    
    # Создаем обновленный объект
    updated_trip = Trip(**trip_dict)
    trips_db[trip_index] = updated_trip
    
    return updated_trip

# 7. УДАЛИТЬ ПОЕЗДКУ
@app.delete("/trips/{trip_id}", tags=["Поездки"])
async def delete_trip(trip_id: str):
    """Удалить поездку по её ID"""
    trip_index = find_trip_index(trip_id)
    
    if trip_index == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Поездка с ID '{trip_id}' не найдена"
        )
    
    # Удаляем из базы данных
    deleted_trip = trips_db.pop(trip_index)
    
    return {
        "message": "Поездка успешно удалена",
        "deleted_trip": deleted_trip.dict()
    }

# 8. СТАТИСТИКА ПО ЧИСЛОВЫМ ПОЛЯМ
@app.get("/statistics", tags=["Статистика"])
async def get_statistics():
    """
    Получить статистику по числовым полям.
    
    Возвращает минимальное, максимальное и среднее значение
    для всех числовых полей модели.
    """
    if not trips_db:
        return {
            "message": "Нет данных для расчета статистики",
            "trip_count": 0
        }
    
    # Определяем числовые поля
    numeric_fields = ['duration_days', 'price', 'rating', 'group_size']
    statistics = {}
    
    for field in numeric_fields:
        # Собираем значения для каждого поля
        values = [getattr(trip, field) for trip in trips_db]
        
        # Вычисляем статистику
        statistics[field] = {
            "min": min(values),
            "max": max(values),
            "average": round(sum(values) / len(values), 2),
            "sum": sum(values),
            "count": len(values)
        }
    
    return {
        "trip_count": len(trips_db),
        "statistics": statistics,
        "calculated_at": get_current_time()
    }

# 9. ПОИСК ПОЕЗДОК ПО ПАРАМЕТРАМ
@app.get("/trips/search", response_model=List[Trip], tags=["Поиск"])
async def search_trips(
    destination: Optional[str] = Query(None, description="Место назначения"),
    country: Optional[str] = Query(None, description="Страна"),
    min_price: Optional[float] = Query(None, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    min_rating: Optional[float] = Query(None, description="Минимальный рейтинг")
):
    """Поиск поездок по различным критериям"""
    results = trips_db.copy()
    
    # Применяем фильтры
    if destination:
        results = [t for t in results if destination.lower() in t.destination.lower()]
    
    if country:
        results = [t for t in results if country.lower() in t.country.lower()]
    
    if min_price is not None:
        results = [t for t in results if t.price >= min_price]
    
    if max_price is not None:
        results = [t for t in results if t.price <= max_price]
    
    if min_rating is not None:
        results = [t for t in results if t.rating >= min_rating]
    
    return results

# 10. ИНФОРМАЦИЯ О ЗДОРОВЬЕ СЕРВИСА
@app.get("/health", tags=["Система"])
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "timestamp": get_current_time(),
        "trip_count": len(trips_db),
        "service": "tourist-trips-api"
    }

# ========== ОБРАБОТЧИКИ ОШИБОК ==========
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "path": request.url.path,
        "timestamp": get_current_time()
    }

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )