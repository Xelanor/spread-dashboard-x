from app.celery import app


from dashboard.dashboard_tasks.bot_page_elements_cacher import BotPageElementsCacher


@app.task(autoretry_for=(), max_retries=0, retry_backoff=False)
def run_bot_page_elements_cacher():
    bot = BotPageElementsCacher()
    bot.run()
