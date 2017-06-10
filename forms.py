from django import forms


class PostForm(forms.Form):
    subject = forms.CharField(label='Subject', max_length=60)
    text = forms.CharField(label='Post', widget=forms.Textarea, max_length=6000)


class ReplyForm(forms.Form):
    text = forms.CharField(label='Reply', widget=forms.Textarea, max_length=6000)
