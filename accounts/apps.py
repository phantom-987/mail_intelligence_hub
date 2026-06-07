from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import os
        # Only start scheduler in the main process, not during migrations/checks
        if os.environ.get('RUN_MAIN') != 'true':
            return
        try:
            from scheduler.apps_ready import start
            start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Scheduler start failed: {e}")