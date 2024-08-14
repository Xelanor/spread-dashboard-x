from app.celery import app

from spread.spread_tasks.fetch_bot_details import fetch_bot_details
from spread.spread_tasks.average_correction import average_correction
from spread.spread_tasks.budget_correction import budget_correction
from spread.spread_tasks.calculate_scores import calculate_scores


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(5, fetch_bot_details.s())
    # sender.add_periodic_task(3 * 60, average_correction.s())
    # sender.add_periodic_task(1 * 60, budget_correction.s())
    # sender.add_periodic_task(10, calculate_scores.s())
