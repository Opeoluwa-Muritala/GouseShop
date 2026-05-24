from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.send_order_confirmation")
def send_order_confirmation(order_id: int) -> dict:
    return {"order_id": order_id, "status": "queued"}


@celery_app.task(name="app.tasks.send_shipping_update")
def send_shipping_update(order_id: int) -> dict:
    return {"order_id": order_id, "status": "queued"}
