from django import forms


class GameScoreForm(forms.Form):
    moves = forms.IntegerField(required=False, min_value=0)
    time = forms.IntegerField(required=False, min_value=0)
    score = forms.IntegerField(required=False, min_value=0)
    total = forms.IntegerField(required=False, min_value=1)
    completed = forms.BooleanField(required=False, initial=True)
    hints_used = forms.IntegerField(required=False, min_value=0, initial=0)
