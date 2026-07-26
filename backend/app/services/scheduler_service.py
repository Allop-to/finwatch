from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.detection_service import run_detection
from app.api.v1.websocket import manager

scheduler = AsyncIOScheduler()


async def scheduled_detection():
    db = SessionLocal()
    try:
        results = await run_detection(db)
        for r in results:
            if r.severity == "high":
                await manager.broadcast({
                    "type": "detection.alert",
                    "data": {
                        "id": r.id, "severity": r.severity,
                        "score": r.anomaly_score, "txn_id": r.transaction_id,
                    },
                })
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        scheduled_detection, "interval", minutes=30, id="incremental_detection",
    )
    scheduler.add_job(
        scheduled_detection, "cron", hour=2, minute=0, id="daily_detection",
    )
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
