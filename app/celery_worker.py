from app import create_app
from app.Mycelery import celery

# Initialize app to set up the application context for tasks
app = create_app()