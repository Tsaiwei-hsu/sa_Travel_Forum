from django.urls import path
from . import views
from posts import views as post_views


urlpatterns = [
    path('list/', views.category_index, name='category_index'),
    path('state/<int:state_id>/', views.filter_by_state, name='filter_by_state'),
    path('city/<int:city_id>/', views.filter_by_city, name='filter_by_city'),
    path('category/<int:category_id>/', views.filter_by_category, name='filter_by_category'),
    path('post_upload/', views.post_upload, name='post_upload'),
]
