from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import State, City, Category, Post

# 首頁 view
def home(request):
    return render(request, 'posts/home.html')

# 類別首頁（選擇州與城市分類）
def category_index(request):
    # 所有州資料
    states = State.objects.all()

    # 州與城市的對應資料（滑過時預覽城市用）
    location_cities = {
        "New South Wales": ["Sydney", "Newcastle", "Wollongong"],
        "Victoria": ["Melbourne", "Geelong", "Ballarat"],
        "Queensland": ["Brisbane", "Gold Coast", "Cairns"],
        "South Australia": ["Adelaide", "Mount Gambier"],
        "Western Australia": ["Perth", "Broome"],
        "Tasmania": ["Hobart", "Launceston"],
        "Northern Territory": ["Darwin", "Alice Springs"],
        "Australian Capital Territory": ["Canberra"]
    }

    return render(request, 'posts/category_index.html', {
        'states': states,
        'location_cities': location_cities
    })

# 根據州 ID 顯示所有城市
def filter_by_state(request, state_id):
    state = get_object_or_404(State, id=state_id)
    cities = City.objects.filter(state=state)
    return render(request, 'posts/city_list.html', {
        'state': state,
        'cities': cities
    })

# 根據城市 ID 顯示可選的分類
def filter_by_city(request, city_id):
    city = get_object_or_404(City, id=city_id)
    categories = Category.objects.all()
    return render(request, 'posts/filter_by_location.html', {
        'city': city,
        'categories': categories,
    })

# 根據分類顯示貼文，可選擇指定城市進一步篩選
def filter_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    city_id = request.GET.get('city_id')

    if city_id:
        city = get_object_or_404(City, id=city_id)
        posts = Post.objects.filter(category=category, city=city)
    else:
        posts = Post.objects.filter(category=category)
        city = None

    return render(request, 'posts/post_list.html', {
        'category': category,
        'posts': posts,
        'city': city,
    })

# 上傳貼文的頁面（表單）
def post_upload(request):
    return render(request, 'posts/post_upload.html')

def is_admin(user):
    return user.is_staff or user.is_superuser

# 新增：待审核贴文列表
@user_passes_test(is_admin)
def review_posts(request):
    posts = Post.objects.filter(is_approved=False)
    return render(request, 'places/review_posts.html', {'posts': posts})

# 新增：通过审核
@user_passes_test(is_admin)
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_approved = True
    post.save()
    return redirect('review_posts')

# 新增：拒绝（删除）贴文
@user_passes_test(is_admin)
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect('review_posts')
