from app.celery import app

from spread.spread_tasks.fetch_bot_details import fetch_bot_details
from spread.spread_tasks.average_correction import average_correction
from spread.spread_tasks.budget_correction import budget_correction
from spread.spread_tasks.calculate_scores import calculate_scores
from spread.spread_tasks.self_new_bot import self_new_bot
from spread.spread_tasks.store_spread_data import store_spread_data


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(5, fetch_bot_details.s())
    sender.add_periodic_task(60, store_spread_data.s())
    # sender.add_periodic_task(3 * 60, average_correction.s())
    # sender.add_periodic_task(1 * 60, budget_correction.s())
    # sender.add_periodic_task(10, calculate_scores.s())
    sender.add_periodic_task(20, self_new_bot.s())
