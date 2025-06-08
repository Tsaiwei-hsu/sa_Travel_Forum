from django.db import models

# 州（省份）模型：代表每個州
class State(models.Model):
    name = models.CharField(max_length=100)  

    def __str__(self):
        return self.name

# 城市模型：與 State 為多對一關係
class City(models.Model):
    name = models.CharField(max_length=100)  #
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')  

    def __str__(self):
        return f"{self.name} ({self.state.name})"

# 類別模型：如 Beaches、Parks 等景點分類
class Category(models.Model):
    name = models.CharField(max_length=100)  

    def __str__(self):
        return self.name

# 貼文模型：包含標題、內容、作者、時間等資訊
class Post(models.Model):
    title = models.CharField(max_length=100)            
    content = models.TextField()                        
    created_at = models.DateTimeField(auto_now_add=True)  
    author = models.CharField(max_length=100)          

    state = models.ForeignKey(State, on_delete=models.CASCADE, default=1)     
    city = models.ForeignKey(City, on_delete=models.CASCADE, default=1)       
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)  
    address = models.CharField(max_length=255, blank=True)  
    is_approved = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    report_reason = models.CharField(max_length=255, blank=True, null=True)  # 新增：檢舉理由
    manual_reviewed = models.BooleanField(default=False)  # 新增：是否已人工審核
    takedown_reason = models.CharField(max_length=255, blank=True, null=True)  # 新增：下架理由

    def __str__(self):
        return self.title
