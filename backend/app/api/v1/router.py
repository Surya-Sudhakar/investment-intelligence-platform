from fastapi import APIRouter

from app.api.v1.routes.assessments import router as assessments_router
from app.api.v1.routes.intelligence import router as intelligence_router
from app.api.v1.routes.market_data import router as market_data_router
from app.api.v1.routes.status import router as status_router

api_router = APIRouter()
api_router.include_router(status_router)
api_router.include_router(market_data_router)
api_router.include_router(intelligence_router)
api_router.include_router(assessments_router)
