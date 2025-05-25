from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django import forms
import os

from .models import Favorite, Post, Location, Category, Photo, UserProfile, Route, RouteItem
from .forms import (
    CustomUserCreationForm, CommentForm, PostForm, PhotoForm, UserProfileForm
)


# 首頁（地圖）
def map_home(request):
    if request.user.is_authenticated:
        UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'posts/home.html')


# 註冊頁面（使用者建立帳號）
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


# 個人檔案設定（可修改資料與頭貼）
@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = ProfileForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "個人資料已更新！")
            return redirect('profile')
        else:
            messages.error(request, "欄位錯誤，請再次檢查。")
    else:
        user_form = ProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)

    my_posts = request.user.post_set.all().order_by('-created_at')
    my_favorites = Favorite.objects.filter(user=request.user).select_related('post')

    return render(request, 'posts/profile.html', {
        'form': user_form,
        'profile_form': profile_form,
        'my_posts': my_posts,
        'favorites': my_favorites,
    })


# 上傳頭像頁
def upload_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        avatar = request.FILES['avatar']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'avatars'))
        filename = fs.save(avatar.name, avatar)
        return redirect('show_avatar', filename=filename)
    return render(request, 'upload_avatar.html')


# 顯示頭像（供預覽）
def show_avatar(request, filename):
    avatar_url = f"{settings.MEDIA_URL}avatars/{filename}"
    return render(request, 'show_avatar.html', {'avatar_url': avatar_url})


# 建立貼文（含多圖）
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            for img in request.FILES.getlist('images'):
                Photo.objects.create(post=post, image=img)
            return redirect('post_list')
        else:
            print("表單錯誤：", form.errors)
    else:
        form = PostForm()

    return render(request, 'posts/create_post.html', {
        'form': form,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'user': request.user
    })


# 編輯貼文（可上傳新圖片）
@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)

    if request.method == 'POST':
        post_form = PostForm(request.POST, instance=post)
        if post_form.is_valid():
            post = post_form.save()
            images = request.FILES.getlist('images')
            if images:
                post.photos.all().delete()
                for img in images:
                    Photo.objects.create(post=post, image=img)
            messages.success(request, "貼文更新成功！")
            return redirect('post_detail', pk=post.pk)
        else:
            print("表單驗證錯誤：", post_form.errors)
            messages.error(request, "表單有誤，請檢查每個欄位。")
    else:
        post_form = PostForm(instance=post)

    return render(request, 'posts/edit_post.html', {
        'form': post_form,
        'photo_form': PhotoForm(),
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'user': request.user,
        'post': post,
    })


# 刪除貼文
@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('profile')


# 單篇貼文詳情（含留言與收藏）
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()

    user_favorites = []
    if request.user.is_authenticated:
        UserProfile.objects.get_or_create(user=request.user)
        user_favorites = Favorite.objects.filter(user=request.user).values_list('post_id', flat=True)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'user_favorites': user_favorites,
    })


# 貼文總清單（可過濾地點與顯示收藏）
def post_list(request):
    location_name = request.GET.get('location')
    if location_name:
        location = get_object_or_404(Location, name=location_name)
        posts = Post.objects.filter(location=location).order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('post_id', flat=True)

    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'selected_location': location_name,
        'current_category': None,
        'user_favorites': user_favorites,
    })


# 根據城市過濾貼文（左側城市選單點擊）
def filter_by_location(request, location_name):
    return HttpResponseRedirect(f"{reverse('post_list')}?location={location_name}")


# 根據分類過濾貼文（左側分類選單點擊）
def filter_by_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    location_name = request.GET.get('location')

    if location_name:
        location = get_object_or_404(Location, name=location_name)
        posts = Post.objects.filter(category=category, location=location).order_by('-created_at')
    else:
        location = None
        posts = Post.objects.filter(category=category).order_by('-created_at')

    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user).values_list('post_id', flat=True)

    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'selected_location': location_name,
        'current_category': category.name,
        'current_city': location.name if location else None,
        'user_favorites': user_favorites,
    })


# 使用者基本資料表單（用於 profile）
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


# 收藏功能切換（AJAX）
@login_required
def toggle_favorite(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, post=post)
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'unfavorited'})
    return JsonResponse({'status': 'favorited'})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Route, RouteItem
from places.models import Post  # 新增：引用景点贴文模型

# 我的路线列表页面
@login_required
def my_routes(request):
    routes = Route.objects.filter(user=request.user)
    return render(request, 'posts/my_routes.html', {'routes': routes})

# 新增路线页面
@login_required
def create_route(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Route.objects.create(user=request.user, name=name)
            return redirect('my_routes')
    return render(request, 'posts/create_route.html')

# 编辑路线名称
@login_required
def edit_route(request, route_id):
    route = get_object_or_404(Route, id=route_id, user=request.user)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            route.name = name
            route.save()
            return redirect('my_routes')
    return render(request, 'posts/edit_route.html', {'route': route})

# 删除路线
@login_required
def delete_route(request, route_id):
    route = get_object_or_404(Route, id=route_id, user=request.user)
    if request.method == 'POST':
        route.delete()
        return redirect('my_routes')
    return render(request, 'posts/delete_route_confirm.html', {'route': route})

# 添加景点到路线
@login_required
def add_place_to_route(request, route_id):
    route = get_object_or_404(Route, id=route_id, user=request.user)
    # 只显示未添加过的景点
    places = Post.objects.exclude(id__in=route.items.values_list('place_id', flat=True))
    if request.method == 'POST':
        place_id = request.POST.get('place_id')
        if place_id:
            order = route.items.count() + 1
            place = get_object_or_404(Post, id=place_id)
            RouteItem.objects.create(route=route, place=place, order=order)
            return redirect('my_routes')
    return render(request, 'posts/add_place_to_route.html', {'route': route, 'places': places})

# 调整路线中景点顺序
@login_required
def edit_route_items(request, route_id):
    route = get_object_or_404(Route, id=route_id, user=request.user)
    items = route.items.all()
    if request.method == 'POST':
        orders = request.POST.getlist('order')
        item_ids = request.POST.getlist('item_id')
        for item_id, order in zip(item_ids, orders):
            item = RouteItem.objects.get(id=item_id, route=route)
            item.order = int(order)
            item.save()
        return redirect('my_routes')
    return render(request, 'posts/edit_route_items.html', {'route': route, 'items': items})
