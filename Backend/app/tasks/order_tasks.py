from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.release_reserved_stock")
def release_reserved_stock() -> dict:
    return {"status": "queued"}


@celery_app.task(name="app.tasks.notify_waitlist")
def notify_waitlist(variant_id: int) -> dict:
    return {"variant_id": variant_id, "status": "queued"}


@celery_app.task(name="app.tasks.charge_preorder_balance")
def charge_preorder_balance(order_id: int) -> dict:
    return {"order_id": order_id, "status": "queued"}
