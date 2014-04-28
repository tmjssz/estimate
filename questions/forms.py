from django.forms import ModelForm

from questions.models import Estimate

class EstimateForm(ModelForm):
    class Meta:
        model = Estimate
        exclude = ('user', 'question', 'date', 'score', 'percentage_error', 'challenge')

    def __init__(self, **kwargs):
        self.__user = kwargs.pop('user', None)
        self.__question = kwargs.pop('question', None)
        self.__challenge = kwargs.pop('challenge', None)
        super(EstimateForm, self).__init__(**kwargs)

    def save(self, commit=True):
        if self.instance.pk is None:
            if self.__user is None:
                raise TypeError("You didn't give an user argument to the constructor.")
            #self.instance.slug = slugify(self.instance.title)
            self.instance.user = self.__user
            self.instance.question = self.__question
            self.instance.challenge = self.__challenge
        return super(EstimateForm, self).save(commit)