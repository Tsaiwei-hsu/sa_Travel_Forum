from .models import Comment, Favorite, Post, Location, Category, Photo, UserProfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import PasswordChangeView
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django import forms
import os
from django.utils import timezone

from .forms import (
    CustomUserCreationForm, CommentForm, PostForm, PhotoForm, UserProfileForm, ReportForm
)

# 使用者基本資料表單（用於 profile）
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

# 首頁
def map_home(request):
    if request.user.is_authenticated:
        UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'posts/home.html')

# 註冊
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            login(request, user)
            return redirect('user_preferences')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

# 個人檔案
@login_required
def profile(request):
    section = request.GET.get('section', 'posts')
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

    deleted_posts = request.user.post_set.filter(is_deleted=True).order_by('-created_at')

    # 只顯示未刪除、已發佈的貼文
    my_posts = request.user.post_set.filter(
        is_draft=False,
        is_deleted=False
    ).order_by('-created_at')

    # 收藏 already filtered by post__is_deleted=False?
    my_favorites = Favorite.objects.filter(
        user=request.user,
        post__is_deleted=False
    ).select_related('post')

    # 草稿、已刪除等維持原樣
    user_drafts = request.user.post_set.filter(
        is_draft=True, is_deleted=False
    ).order_by('-created_at')
    deleted_posts = request.user.post_set.filter(
        is_deleted=True
    ).order_by('-created_at')

    return render(request, 'posts/profile.html', {
        'section': section,
        'form': user_form,
        'profile_form': profile_form,
        'my_posts': my_posts,
        'favorites': my_favorites,
        'user_drafts': user_drafts,
        'deleted_posts': deleted_posts,
    })

# 建立貼文（多圖）
@login_required
def create_post(request):
    if request.method == 'POST' and 'cancel' in request.POST:
        return redirect('post_list')

    if request.method == 'POST':
        form = PostForm(request.POST)
        # 儲存草稿
        if 'save_draft' in request.POST:
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.is_draft = True
                post.save()
                for img in request.FILES.getlist('images'):
                    Photo.objects.create(post=post, image=img)
                messages.success(request, "草稿已儲存！")
                return redirect('/profile/?section=drafts')
            else:
                # 檢查是否為違規詞錯誤
                violation_msgs = [e for errs in form.errors.values() for e in errs if '違規詞' in str(e)]
                if violation_msgs:
                    for msg in violation_msgs:
                        messages.error(request, msg)
                else:
                    messages.error(request, "草稿儲存失敗，請檢查輸入。")
        # 發佈貼文
        else:
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.is_draft = False
                post.save()
                for img in request.FILES.getlist('images'):
                    Photo.objects.create(post=post, image=img)
                messages.success(request, "貼文已發佈！")
                return redirect('post_list')
            else:
                violation_msgs = [e for errs in form.errors.values() for e in errs if '違規詞' in str(e)]
                if violation_msgs:
                    for msg in violation_msgs:
                        messages.error(request, msg)
                else:
                    messages.error(request, "發布失敗，請確認表單輸入是否正確。")
    else:
        form = PostForm()

    return render(request, 'posts/create_post.html', {
        'form': form,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
    })


# 編輯貼文
@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES, instance=post)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            rate_posta = request.POST.get('rate_posta')
            post.rate_posta = float(rate_posta) if rate_posta else None
            # 若該貼文曾被軟刪除，重新編輯時自動恢復顯示，並重設所有審核欄位
            if post.is_deleted:
                post.is_deleted = False
                post.takedown_reason = None
                post.is_approved = False
                post.manual_reviewed = False
                post.is_reported = False
                post.report_reason = None
            post.save()
            for img in request.FILES.getlist('images'):
                Photo.objects.create(post=post, image=img)
            messages.success(request, "貼文更新成功！")
            return redirect('post_detail', pk=post.pk)
    else:
        post_form = PostForm(instance=post)

    return render(request, 'posts/edit_post.html', {
        'form': post_form,
        'photo_form': PhotoForm(),
        'post': post,
        'photos': post.photos.all(),
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
    })

# 編輯草稿
@login_required
def edit_draft(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user, is_draft=True)

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES, instance=post)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            rate_posta = request.POST.get('rate_posta')
            post.rate_posta = float(rate_posta) if rate_posta else None
            if 'publish' in request.POST:
                post.is_draft = False
            post.save()
            for img in request.FILES.getlist('images'):
                Photo.objects.create(post=post, image=img)
            return redirect('post_detail', pk=post.pk) if not post.is_draft else redirect('/profile/?section=drafts')
    else:
        post_form = PostForm(instance=post)

    return render(request, 'posts/edit_draft.html', {
        'form': post_form,
        'photo_form': PhotoForm(),
        'post': post,
        'photos': post.photos.all(),
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
    })

# 建立草稿
@login_required
def create_draft(request):
    post = Post.objects.create(author=request.user, is_draft=True)
    return redirect('edit_draft', pk=post.pk)

# 刪除圖片（共用）
@login_required
def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    if photo.post.author != request.user:
        return HttpResponseForbidden("你無權刪除此圖片")
    photo.delete()
    return JsonResponse({'status': 'success'})

# 刪除貼文
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)

    if request.method == 'POST':
        post.is_deleted = True
        post.save()
        if post.is_draft:
            messages.success(request, "草稿已刪除")
            return redirect('/profile/?section=drafts')
        else:
            messages.success(request, "貼文已刪除")
            return redirect('/profile/?section=posts')
    else:
        messages.error(request, "刪除失敗：必須透過 POST 請求")
        return redirect('post_detail', pk=pk)

# 單篇詳情
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.is_deleted:
        if request.user != post.author:
            return render(request, 'posts/post_deleted.html', {'post': post})
    comments = post.comments.all()
    user_favorites = Favorite.objects.filter(user=request.user).values_list('post_id', flat=True) if request.user.is_authenticated else []

    # 平均留言評分（只計算有評分的留言）
    rated_comments = [c for c in comments if c.rate_comment]
    if rated_comments:
        avg_comment_rating = round(sum(c.rate_comment for c in rated_comments) / len(rated_comments), 2)
    else:
        avg_comment_rating = None

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            # 額外處理 rate_comment
            rate_comment = request.POST.get('rating') or request.POST.get('rate_comment')
            if rate_comment:
                comment.rate_comment = int(rate_comment)
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'user_favorites': user_favorites,
        'avg_comment_rating': avg_comment_rating,
    })

# 貼文列表 - 主要整合篩選功能
from django.shortcuts import render, get_object_or_404
from .models import Location, Category, Post, Favorite

from django.shortcuts import render, get_object_or_404
from .models import Post, Location, Category, Favorite

def post_list(request):
    selected_location = request.GET.get('location', '')
    selected_type = request.GET.get('location_type', '')
    selected_category_id = request.GET.get('category', '')

    posts = Post.objects.filter(is_draft=False, is_deleted=False).order_by('-created_at')

    if selected_location:
        posts = posts.filter(location__name=selected_location)

    if selected_type in ['indoor', 'outdoor']:
        posts = posts.filter(category__location_type=selected_type)

    current_category = None
    if selected_category_id:
        try:
            category = Category.objects.get(pk=selected_category_id)
            posts = posts.filter(category=category)
            current_category = category.name
        except Category.DoesNotExist:
            current_category = None

    locations = Location.objects.all()
    indoor_categories = Category.objects.filter(location_type='indoor')
    outdoor_categories = Category.objects.filter(location_type='outdoor')

    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = Favorite.objects.filter(user=request.user, post__is_deleted=False).values_list('post_id', flat=True)

    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'locations': locations,
        'indoor_categories': indoor_categories,
        'outdoor_categories': outdoor_categories,
        'selected_location': selected_location,
        'selected_type': selected_type,
        'current_category': current_category,
        'user_favorites': user_favorites,
    })



# 收藏切換
@login_required
def toggle_favorite(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, post=post)
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'unfavorited'})
    return JsonResponse({'status': 'favorited'})

# 過濾：地點
def filter_by_category(request, category_id):
    params = request.GET.copy()
    params['category'] = category_id
    url = reverse('post_list') + '?' + params.urlencode()
    return redirect(url)


def filter_by_location_type(request, location_type):
    params = request.GET.copy()
    params['location_type'] = location_type
    url = reverse('post_list') + '?' + params.urlencode()
    return redirect(url)


# 過濾：位置類型 (Indoor/Outdoor) - 可以刪除這個函數，因為功能已整合到 post_list
def filter_by_location_type(request, location_type):
    location_name = request.GET.get('location')
    posts = Post.objects.filter(
        is_draft=False, 
        is_deleted=False,
        category__location_type=location_type
    ).order_by('-created_at')
    
    if location_name:
        location = get_object_or_404(Location, name=location_name)
        posts = posts.filter(location=location)

    user_favorites = Favorite.objects.filter(user=request.user, post__is_deleted=False).values_list('post_id', flat=True) if request.user.is_authenticated else []

    # 取得所有分類資料，分別傳給模板
    indoor_categories = Category.objects.filter(location_type='indoor')
    outdoor_categories = Category.objects.filter(location_type='outdoor')

    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'indoor_categories': indoor_categories,
        'outdoor_categories': outdoor_categories,
        'selected_location': location_name,
        'selected_location_type': location_type,
        'current_location_type': location_type.title(),
        'user_favorites': user_favorites,
    })

# 刪除留言
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.post.author != request.user:
        return HttpResponseForbidden("你無權刪除此留言")
    post_id = comment.post.id
    comment.delete()
    messages.success(request, "留言已刪除")
    return redirect('post_detail', pk=post_id)

# 修改密碼
class MyPasswordChangeView(PasswordChangeView):
    template_name = 'registration/change_password.html'  
    success_url = reverse_lazy('profile')  

    def form_valid(self, form):
        messages.success(self.request, '密碼已成功修改')
        return super().form_valid(form)
    
# 檢舉貼文
@login_required
def report_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            post.is_reported = True
            post.report_reason = form.cleaned_data['reason']
            post.report_time = timezone.now()
            post.save()
            return redirect('post_detail', pk=pk)
    else:
        form = ReportForm()
    return render(request, 'posts/report_post.html', {'form': form, 'post': post})

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def manual_review_list(request):
    posts = Post.objects.filter(is_reported=True, manual_reviewed=False)
    return render(request, 'posts/manual_review_list.html', {'posts': posts})

@staff_member_required
def manual_review_action(request, pk, action):
    post = get_object_or_404(Post, pk=pk)
    if action == 'approve':
        post.is_approved = True
        post.takedown_reason = None
    elif action == 'reject':
        post.is_approved = False
        post.takedown_reason = "因不符合規定而被下架"
    post.manual_reviewed = True
    post.save()
    return redirect('manual_review_list')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserPreference
from .forms import PreferencesForm

@login_required
def user_preferences(request):
    # 只有在剛註冊或強制填寫時導向到這裡
    pref, _ = UserPreference.objects.get_or_create(user=request.user)
    indoor_cats  = Category.objects.filter(location_type='indoor')
    outdoor_cats = Category.objects.filter(location_type='outdoor')

    if request.method == 'POST':
        # 直接用 instance 讓 ModelForm 處理 M2M 存取
        form = PreferencesForm(request.POST, instance=pref)
        if form.is_valid():
            form.save()
            messages.success(request, "偏好已儲存")
            return redirect('post_list') # 儲存完導向首頁或任意頁面
    else:
        form = PreferencesForm(instance=pref)

    
    return render(request, 'posts/preferences.html', {
        'form': form,
        'indoor_cats': indoor_cats,
        'outdoor_cats': outdoor_cats,
    })