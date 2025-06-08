from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'author', 'is_reported_zh', 'report_reason', 'report_time', 'manual_reviewed_zh', 'is_approved_zh', 'is_deleted_zh', 'created_at'
    )
    list_filter = (
        'is_reported', 'manual_reviewed', 'is_approved', 'is_deleted', 'created_at', 'category', 'location'
    )
    search_fields = ('title', 'content', 'author__username', 'report_reason')
    readonly_fields = ('created_at', 'report_time',)
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'author', 'category', 'location', 'address', 'rate_posta', 'created_at')
        }),
        ('審核與狀態', {
            'fields': ('is_reported', 'report_reason', 'report_time', 'manual_reviewed', 'is_approved', 'takedown_reason', 'is_deleted')
        }),
    )
    actions = ["approve_selected", "reject_selected"]

    def save_model(self, request, obj, form, change):
        # 若管理員在 admin 後台將 is_deleted 從 True 改為 False，則自動重設審核欄位
        if change:
            old_obj = Post.objects.get(pk=obj.pk)
            if old_obj.is_deleted and not obj.is_deleted:
                obj.takedown_reason = None
                obj.is_approved = False
                obj.manual_reviewed = False
                obj.is_reported = False
                obj.report_reason = None
        super().save_model(request, obj, form, change)

    @admin.action(description='批次通過審核')
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True, manual_reviewed=True, takedown_reason=None)

    @admin.action(description='批次刪除(下架)')
    def reject_selected(self, request, queryset):
        queryset.update(is_approved=False, manual_reviewed=True, is_deleted=True, takedown_reason="因不符合規定而被下架")

    def get_field_queryset(self, db, db_field, request):
        return super().get_field_queryset(db, db_field, request)
    def get_changelist(self, request, **kwargs):
        from django.contrib.admin.views.main import ChangeList
        class MyChangeList(ChangeList):
            def get_results(self, *args, **kwargs):
                super().get_results(*args, **kwargs)
                # ...existing code...
        return MyChangeList
    def is_reported_zh(self, obj):
        return '已檢舉' if obj.is_reported else '—'
    is_reported_zh.short_description = '檢舉狀態'
    def manual_reviewed_zh(self, obj):
        if obj.manual_reviewed:
            return '已審核'
        return '-'
    manual_reviewed_zh.short_description = '審核狀態'
    manual_reviewed_zh.allow_tags = True
    def is_approved_zh(self, obj):
        # 若被檢舉且尚未審核，顯示未審核
        if obj.is_reported and not obj.manual_reviewed:
            return '未審核'
        if not obj.manual_reviewed:
            return '—'
        return '通過' if obj.is_approved else '未通過'
    is_approved_zh.short_description = '審核結果'
    def is_deleted_zh(self, obj):
        return '已刪除' if obj.is_deleted else '—'
    is_deleted_zh.short_description = '刪除狀態'