from django import forms
from .models import Post, Comment, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Photo


# 貼文內容表單（標題、內容、分類、地點、地址）
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'location', 'category', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True  # 強制所有欄位必填

# 支援多圖上傳的檔案元件
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# 留言表單（只包含內容欄位）
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '寫下你的留言…'
            }),
        }

# 自定義使用者註冊表單（加入 email）
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# 編輯使用者基本資料（帳號、email）
class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email']

# 編輯使用者個人資料（頭像）
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',  
                'onchange': 'previewAvatar(event)'  
            }),
        }


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']
