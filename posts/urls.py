from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from .views import MyPasswordChangeView

urlpatterns = [
    # 首頁（地圖首頁）
    path('', views.map_home, name='home'),

    # 貼文功能
    path('posts/', views.post_list, name='post_list'),               # 貼文列表
    path('post/<int:pk>/', views.post_detail, name='post_detail'),   # 單篇貼文詳情
    path('create/', views.create_post, name='create_post'),          # 建立貼文
    path('edit/<int:pk>/', views.edit_post, name='edit_post'),       # 編輯貼文
    path('delete/<int:pk>/', views.delete_post, name='delete_post'), # 刪除貼文
    path('favorite/<int:post_id>/', views.toggle_favorite, name='toggle_favorite'), # 收藏貼文
    path('profile/', views.profile, name='profile'),
    path('draft/<int:pk>/edit/', views.edit_draft, name='edit_draft'), # 編輯草稿
    path('delete_photo/<int:photo_id>/', views.delete_photo, name='delete_photo'), #刪除圖片
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'), # 刪除留言





    # 使用者帳號功能
    path('signup/', views.signup, name='signup'),                          # 註冊
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),  # 登出
    path('accounts/password_change/', MyPasswordChangeView.as_view(), name='password_change'),
    path('accounts/', include('django.contrib.auth.urls')),                # Django 內建登入/密碼變更等
    

    # 個人資料與頭像
    path('profile/', views.profile, name='profile'),                       # 使用者個人資料頁

    # 分類與篩選功能
    path('location/<int:location_id>/', views.filter_by_location, name='filter_by_location'),  # 地點篩選
    path('category/<int:category_id>/', views.filter_by_category, name='filter_by_category'),  # 分類篩選
]

# 開發環境媒體檔案處理（DEBUG 模式下啟用）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
