from celery import shared_task
from .models import Post

@shared_task
def publish_scheduled_posts():
    Post.publish_scheduled()
