from django.contrib import admin
from .models import Post

# 新增：后台审核景点贴文
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_approved', 'created_at')  # 显示审核状态
    list_filter = ('is_approved',)  # 可筛选审核状态
    actions = ['approve_posts']  # 批量审核操作

    def approve_posts(self, request, queryset):
        queryset.update(is_approved=True)
    approve_posts.short_description = "批量通过审核"