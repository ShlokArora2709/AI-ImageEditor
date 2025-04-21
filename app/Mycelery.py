from celery import Celery
import os
celery = Celery(
        'app',
        broker="redis://default:AT_uAAIjcDFkMGZmODY4Njg1ZDU0NWU3OGQwMmQ4NzBmNzEyYWU4M3AxMA@relaxing-mudfish-16366.upstash.io:6379",
        backend="redis://localhost:6379/0",
    )
def configure_celery(app):
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery