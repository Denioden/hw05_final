from django import forms
from .models import Post
from .models import Comment


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = "Группа не выбрана"

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Изображение'
        }
        help_texts = {
            'group': 'Выберите группу, к которой будет относиться пост.',
            'text': 'Введите текст нового поста.',
            'image': 'Выберитре изображение'
        }
        widgets = {
            'text': forms.Textarea(attrs={'cols': 40, 'rows': 10})
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}
