from fastapi import APIRouter
from app.api.v1.transactions import router as txn_router
from app.api.v1.categories import router as cat_router
from app.api.v1.budget import router as budget_router
from app.api.v1.imports import router as import_router
from app.api.v1.detection import router as detection_router
from app.api.v1.websocket import router as ws_router
from app.api.v1.llm import router as llm_router
from app.api.v1.rules import router as rules_router

api_router = APIRouter()
api_router.include_router(txn_router)
api_router.include_router(cat_router)
api_router.include_router(budget_router)
api_router.include_router(import_router)
api_router.include_router(detection_router)
api_router.include_router(ws_router)
api_router.include_router(llm_router)
api_router.include_router(rules_router)
