from django import forms
from .models import (
    World, Chapter, Lesson, LessonContent, Vocabulary,
    VocabularyCategory, Quiz, Exam, Badge
)


class WorldForm(forms.ModelForm):
    class Meta:
        model = World
        fields = [
            'name', 'name_fa', 'description', 'difficulty_level',
            'order', 'image', 'background_image', 'map_svg',
            'xp_reward', 'coin_reward', 'is_published'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_fa': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'coin_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = [
            'name', 'name_fa', 'description', 'order', 'unlock_score',
            'required_chapter', 'xp_reward', 'coin_reward',
            'passing_score', 'estimated_time_minutes', 'image', 'is_published'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_fa': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'unlock_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'coin_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_time_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_chapter': forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'name', 'name_fa', 'lesson_type', 'order', 'xp_reward',
            'coin_reward', 'estimated_time_minutes', 'is_published', 'is_free_preview',
            'is_exclusive'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_fa': forms.TextInput(attrs={'class': 'form-control'}),
            'lesson_type': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'coin_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_time_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_free_preview': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_exclusive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LessonContentForm(forms.ModelForm):
    image_width = forms.IntegerField(
        required=False, min_value=20, max_value=100, initial=100,
        label='عرض عکس شاخص (٪)',
        help_text='درصد عرض عکس شاخص نسبت به متن درس (۲۰ تا ۱۰۰)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 20, 'max': 100}))
    image_align = forms.ChoiceField(
        required=False, initial='center', label='محل قرارگیری عکس',
        choices=(('right', 'راست'), ('center', 'وسط'), ('left', 'چپ')),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='عکس شاخص در متن درس کجا قرار بگیرد')

    class Meta:
        model = LessonContent
        fields = [
            'introduction', 'introduction_audio', 'learning_objectives',
            'grammar_notes', 'grammar_examples', 'example_sentences',
            'featured_image', 'featured_video', 'featured_video_url',
            'summary', 'key_takeaways', 'is_interactive', 'allow_skip'
        ]
        widgets = {
            'introduction': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'grammar_notes': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'learning_objectives': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter each objective on a new line'}),
            'grammar_examples': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter each example on a new line'}),
            'example_sentences': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter each sentence on a new line'}),
            'key_takeaways': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter each takeaway on a new line'}),
            'featured_video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_interactive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_skip': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fname in ('introduction', 'summary', 'learning_objectives', 'grammar_examples',
                      'example_sentences', 'key_takeaways'):
            self.fields[fname].required = False

    def clean(self):
        cleaned = super().clean()
        for fname in ('learning_objectives', 'grammar_examples', 'example_sentences', 'key_takeaways'):
            if cleaned.get(fname) in (None, '', 'null'):
                cleaned[fname] = []
        return cleaned


class VocabularyForm(forms.ModelForm):
    class Meta:
        model = Vocabulary
        fields = [
            'word', 'pronunciation', 'meaning', 'meaning_fa',
            'part_of_speech', 'difficulty', 'categories',
            'audio_uk', 'audio_us', 'audio_example', 'image', 'is_active'
        ]
        widgets = {
            'word': forms.TextInput(attrs={'class': 'form-control'}),
            'pronunciation': forms.TextInput(attrs={'class': 'form-control'}),
            'meaning': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'meaning_fa': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'part_of_speech': forms.TextInput(attrs={'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VocabularyCategoryForm(forms.ModelForm):
    class Meta:
        model = VocabularyCategory
        fields = ['name', 'name_fa', 'description', 'icon', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_fa': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Font Awesome class (e.g., fas fa-plane)'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'lesson', 'title', 'description', 'passing_score', 'time_limit_minutes',
            'max_attempts', 'shuffle_questions', 'xp_reward',
            'coin_reward', 'is_published'
        ]
        widgets = {
            'lesson': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'value': 70}),
            'time_limit_minutes': forms.NumberInput(attrs={'class': 'form-control', 'value': 10}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'value': 3}),
            'shuffle_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control', 'value': 30}),
            'coin_reward': forms.NumberInput(attrs={'class': 'form-control', 'value': 15}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'exam_type', 'chapter', 'world', 'title', 'description',
            'passing_score', 'time_limit_minutes', 'max_attempts',
            'questions_count', 'randomize_questions', 'xp_reward',
            'coin_reward', 'is_published'
        ]
        widgets = {
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'chapter': forms.Select(attrs={'class': 'form-select'}),
            'world': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_limit_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'questions_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'randomize_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'coin_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = [
            'name', 'name_fa', 'description', 'badge_type',
            'icon', 'requirement_type', 'requirement_value',
            'xp_reward', 'is_active', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_fa': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'badge_type': forms.Select(attrs={'class': 'form-select'}),
            'requirement_type': forms.TextInput(attrs={'class': 'form-control'}),
            'requirement_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
