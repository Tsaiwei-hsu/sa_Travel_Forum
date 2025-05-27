from django.db import models
from django.contrib.auth.models import User

# 地點模型（城市、州名等）
class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# 分類模型（如：Beaches, Museums）
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# 主要貼文模型
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)  
    title = models.CharField(max_length=200)                    
    content = models.TextField()                               
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)  
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)  
    address = models.CharField(max_length=255, blank=True)     
    created_at = models.DateTimeField(auto_now_add=True)       
    is_draft = models.BooleanField(default=False) 

    def __str__(self):
        return self.title

# 貼文圖片模型（多張圖片對應一篇貼文）
class Photo(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='photos')  
    image = models.ImageField(upload_to='post_photos/')  #

# 留言模型（多則留言對應一篇貼文）
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"

# 使用者擴充資料（例如頭貼）
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  

    def __str__(self):
        return self.user.username

# models.py
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # 防止重複收藏

# 使用者喜好
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorite_categories = models.ManyToManyField(Category, blank=True)  # 使用者喜好的分類
    favorite_locations = models.ManyToManyField(Location, blank=True)  # 使用者喜好的地點

    def __str__(self):
        return f"{self.user.username}的喜好"