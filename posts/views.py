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
            return redirect('home')
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

    my_posts = request.user.post_set.filter(is_draft=False).order_by('-created_at')
    user_drafts = request.user.post_set.filter(is_draft=True, is_deleted=False).order_by('-created_at') 
    my_favorites = Favorite.objects.filter(user=request.user, post__is_deleted=False).select_related('post')
    deleted_posts = request.user.post_set.filter(is_deleted=True).order_by('-created_at')

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
    if request.method == 'POST':
        if 'cancel' in request.POST:
            return redirect('post_list')

        if 'save_draft' in request.POST:
            # 草稿允許空欄位，但至少要填一個欄位
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            location = request.POST.get('location')
            category = request.POST.get('category')
            address = request.POST.get('address', '').strip()
            rate_posta = request.POST.get('rate_posta')
            if not (title or content or location or category or address):
                messages.error(request, "請至少填寫一個欄位再儲存草稿！")
                form = PostForm(request.POST)
                return render(request, 'posts/create_post.html', {
                    'form': form,
                    'locations': Location.objects.all(),
                    'categories': Category.objects.all(),
                })
            post = Post(author=request.user, is_draft=True)
            post.title = title
            post.content = content
            post.location_id = location or None
            post.category_id = category or None
            post.address = address
            post.rate_posta = float(rate_posta) if rate_posta else None
            post.save()
            for img in request.FILES.getlist('images'):
                Photo.objects.create(post=post, image=img)
            messages.success(request, "草稿已儲存！")
            return redirect('/profile/?section=drafts')
        else:
            form = PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.is_draft = False
                rate_posta = request.POST.get('rate_posta')
                post.rate_posta = float(rate_posta) if rate_posta else None
                post.save()
                for img in request.FILES.getlist('images'):
                    Photo.objects.create(post=post, image=img)
                messages.success(request, "貼文已發佈！")
                return redirect('post_list')
            else:
                messages.error(request, "表單錯誤，請確認欄位")
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
            messages.success(request, "草稿已刪除（僅自己可見）")
            return redirect('/profile/?section=drafts')
        else:
            messages.success(request, "貼文已刪除（僅自己可見）")
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

# 貼文列表
def post_list(request):
    location_name = request.GET.get('location')
    posts = Post.objects.filter(is_draft=False, is_deleted=False).order_by('-created_at')
    if location_name:
        location = get_object_or_404(Location, name=location_name)
        posts = posts.filter(location=location)

    user_favorites = Favorite.objects.filter(user=request.user, post__is_deleted=False).values_list('post_id', flat=True) if request.user.is_authenticated else []

    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'selected_location': location_name,
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

# 過濾：地點與分類
def filter_by_location(request, location_name):
    return HttpResponseRedirect(f"{reverse('post_list')}?location={location_name}")

def filter_by_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    location_name = request.GET.get('location')
    posts = Post.objects.filter(category=category).order_by('-created_at')
    if location_name:
        location = get_object_or_404(Location, name=location_name)
        posts = posts.filter(location=location)

    user_favorites = Favorite.objects.filter(user=request.user).values_list('post_id', flat=True) if request.user.is_authenticated else []

    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'selected_location': location_name,
        'current_category': category.name,
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