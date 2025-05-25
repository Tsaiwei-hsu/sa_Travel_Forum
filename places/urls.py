from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.category_index, name='category_index'),
    path('state/<int:state_id>/', views.filter_by_state, name='filter_by_state'),
    path('city/<int:city_id>/', views.filter_by_city, name='filter_by_city'),
    path('category/<int:category_id>/', views.filter_by_category, name='filter_by_category'),
    path('post_upload/', views.post_upload, name='post_upload'),
    path('review_posts/', views.review_posts, name='review_posts'),  # 待审核贴文列表
    path('approve_post/<int:post_id>/', views.approve_post, name='approve_post'),  # 通过审核
    path('reject_post/<int:post_id>/', views.reject_post, name='reject_post'),  # 删除贴文
]
