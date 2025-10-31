from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating','text']
        widgets = {
            'text': forms.Textarea(attrs={'rows':3,'placeholder':'Ваш відгук...','class':"w-full border border-gray-300 rounded-md p-3 text-sm focus:ring-2 focus:ring-black focus:border-black"}),
            'rating': forms.NumberInput(attrs={'class':'hidden peer'}),
        }