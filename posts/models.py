from django.db import models
from django.contrib.auth.models import User

# 城市模型
class Location(models.Model):
    name = models.CharField("城市名稱", max_length=100)
    def __str__(self):
        return self.name

# 室內 / 戶外 分類模型（10 筆預先建立）
class Category(models.Model):
    LOCATION_TYPE_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
    ]
    name = models.CharField("分類名稱", max_length=100)
    location_type = models.CharField(
        "環境類型",
        max_length=10,
        choices=LOCATION_TYPE_CHOICES,
        default='indoor',
    )
    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"

# 主要貼文模型
class Post(models.Model):
    author   = models.ForeignKey(User, on_delete=models.CASCADE)
    title    = models.CharField(max_length=200)
    content  = models.TextField()
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=255, blank=True)     
    created_at = models.DateTimeField(auto_now_add=True)       
    is_draft = models.BooleanField(default=False)
    rate_posta = models.FloatField(null=True, blank=True, help_text="上傳者評分，可不填")
    is_reported = models.BooleanField(default=False)
    report_reason = models.CharField(max_length=255, blank=True, null=True)
    report_time = models.DateTimeField(null=True, blank=True, help_text="檢舉時間")
    manual_reviewed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    takedown_reason = models.CharField(max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField(default=False, help_text="軟刪除：被刪除則不顯示於前台")
    

    def __str__(self):
        return self.title

# 貼文圖片模型（多張圖片對應一篇貼文）
class Photo(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='post_photos/')

# 留言模型（多則留言對應一篇貼文）
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rate_comment = models.PositiveSmallIntegerField(null=True, blank=True, help_text="留言評分，可不填")

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"

# 使用者擴充資料（例如頭貼）
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  
    interests = models.CharField(max_length=200, blank=True)
    want_email_notifications = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username

# 收藏
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # 防止重複收藏
    

class UserPreference(models.Model):
    user                = models.OneToOneField(User, on_delete=models.CASCADE)
    favorite_locations  = models.ManyToManyField(Location, blank=True, verbose_name="喜歡的城市")
    favorite_categories = models.ManyToManyField(Category, blank=True, verbose_name="喜歡的環境分類")
    def __str__(self):
        return f"{self.user.username} 的喜好"