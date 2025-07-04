from django import forms
from .models import Post, Comment, UserProfile, Photo
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import UserPreference, Location, Category


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

        # 除了 rate_posta 與 images，其餘皆為必填
        for name, field in self.fields.items():
            if name not in ['rate_posta', 'images']:
                field.required = True
        self.fields['rate_posta'].required = False

        # ✅ 保證 category 一定包含原本的值（避免編輯時出錯）
        original_category = self.instance.category if self.instance and self.instance.pk else None
        categories = Category.objects.all()

        if original_category and original_category not in categories:
            categories = Category.objects.filter(pk=original_category.pk) | categories

        self.fields['category'].queryset = categories.distinct()

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

# posts/forms.py
from django import forms
from .models import UserPreference, Location, Category

from django import forms
from .models import UserPreference, Category, Location

class PreferencesForm(forms.ModelForm):
    favorite_locations = forms.ModelMultipleChoiceField(
        queryset=Location.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple',
            'size': 5,
        }),
        label='喜歡的城市',
        required=False,
    )

    indoor_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple',
            'size': 5,
        }),
        label='喜歡的室內分類',
        required=False,
    )

    outdoor_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple',
            'size': 5,
        }),
        label='喜歡的室外分類',
        required=False,
    )

    class Meta:
        model = UserPreference
        fields = ['favorite_locations', 'indoor_categories', 'outdoor_categories']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['indoor_categories'].queryset = Category.objects.filter(location_type='indoor')
        self.fields['outdoor_categories'].queryset = Category.objects.filter(location_type='outdoor')
