from django import forms
from .models import Post, Comment, UserProfile, Photo
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# 違規詞列表，可擴充
BAD_WORDS = ['血腥', '暴力', '色情', '殺', '強姦', '裸', '屍體']

# 支援多圖上傳的 FileInput
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# 貼文表單
class PostForm(forms.ModelForm):
    # 自訂多檔上傳欄位
    images = forms.FileField(
        widget=MultiFileInput,
        required=False,
        label='Images'
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'location', 'category', 'address', 'rate_posta']
        widgets = {
            'rate_posta': forms.HiddenInput(),  # 星級輸入隱藏
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 除了 rate_posta 與 images，欄位皆為必填
        for name, field in self.fields.items():
            if name not in ['rate_posta', 'images']:
                field.required = True
        self.fields['rate_posta'].required = False

    def clean(self):
        cleaned = super().clean()
        title = cleaned.get('title', '') or ''
        content = cleaned.get('content', '') or ''
        combined = f"{title} {content}".lower()
        for word in BAD_WORDS:
            if word in combined:
                raise forms.ValidationError(f'內容含有違規詞彙：「{word}」')
        return cleaned

    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        for word in BAD_WORDS:
            if word in title.lower():
                raise forms.ValidationError(f'標題含有違規詞彙：「{word}」')
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        for word in BAD_WORDS:
            if word in content.lower():
                raise forms.ValidationError(f'內容含有違規詞彙：「{word}」')
        return content

# 留言表單
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'rate_comment']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': '請勿輸入違規詞彙'})
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        for word in BAD_WORDS:
            if word in content:
                raise forms.ValidationError(f'內容含有違規詞彙：「{word}」')
        return content

# 使用者註冊表單
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# 編輯個人資料
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'onchange': 'previewAvatar(event)'
            })
        }

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']


class ReportForm(forms.Form):
    reason = forms.CharField(label="檢舉理由", max_length=255, widget=forms.Textarea)


class PreferencesForm(forms.Form):
    # 根據你的需求定義欄位，示例用興趣與通知開關
    interests = forms.CharField(label="興趣（逗號分隔）", max_length=200)
    want_email_notifications = forms.BooleanField(label="希望接收電子郵件通知", required=False)
