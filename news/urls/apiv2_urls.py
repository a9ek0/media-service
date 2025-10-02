from django.urls import path
from news.views import apiv2_views

urlpatterns = [
    path('news/feed/', apiv2_views.NewsFeedAPIView.as_view(), name='news-feed'),
    path('news/<int:newsItemId>/', apiv2_views.news_detail_html, name='news-detail'),
    path('news/categories/', apiv2_views.NewsCategoriesAPIView.as_view(), name='news-categories'),
]
