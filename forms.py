from django import forms


class PostForm(forms.Form):
    subject = forms.CharField(label='Subject', widget=forms.Textarea(attrs={'rows': 1, 'cols': 80}), max_length=60)
    text = forms.CharField(label='Post', widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}), max_length=6000)


class ReplyForm(forms.Form):
    text = forms.CharField(label='', widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}), max_length=6000)
