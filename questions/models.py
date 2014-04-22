# encoding: utf-8
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
import math


# =============================================================================
# QUESTION MODEL
# =============================================================================
class Question(models.Model):
    """Question model."""
    title = models.CharField(u'Titel', max_length=100, help_text="Bitte einen Titel für die Frage eingeben (mit max. 100 Zeichen).")
    question = models.TextField(u'Frage', help_text="Bitte hier die Schätz-Frage eingeben. Es sind nur Fragen mit numerischen Antworten erlaubt.")
    answer = models.FloatField(verbose_name=u'Antwort', help_text="Bitte hier eine gültige Antwort eingeben. (Nur numerische Werte sind möglich)")
    unit = models.CharField(u'Einheit', max_length=100, help_text="Hier kann angegeben werden in welcher Einheit der Schätzwert sein soll. (optional)", blank=True, null=True)
    image = models.ImageField(u'Bild', help_text='Hier kann ein Bild hochgeladen werden. (optional)', upload_to='static/img/', blank=True, null=True)
    published = models.BooleanField(verbose_name=u'Veröffentlicht', default=True)
    stats = models.BooleanField(verbose_name=u'Statistik', default=False,  help_text='Soll diese Frage in die Statistiken einbezogen werden?')
    author = models.ForeignKey(User, verbose_name=u'Autor')
    slug = models.SlugField(unique=True)
    date_created = models.DateTimeField(editable=False, verbose_name=u'Erstellt')
    date_updated = models.DateTimeField(editable=False, verbose_name=u'Zuletzt Geändert')
    
    class Meta:
        verbose_name = u'Frage'
        verbose_name_plural = u'Fragen'
        ordering = ['-date_created']

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.id:
            self.date_created = now()
        self.date_updated = now()
        super(Question, self).save(*args, **kwargs)
        
        estimates = Estimate.objects.filter(question=self.id)
        for e in estimates:
            e.update_percentage_error()
            e.update_score()

    @models.permalink
    def get_absolute_url(self):
        return ('questions_question_show', (), {'slug': self.slug})


# =============================================================================
# ESTIMATE MODEL
# =============================================================================
class EstimateManager(models.Manager):
    
    def get_avg_estimates(self):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.question_id, AVG(e.estimate) as estimate, AVG(e.score) as score, 100*ABS(q.answer-AVG(e.estimate))/q.answer as percentage_error 
            FROM questions_estimate e, questions_question q
            WHERE q.id == e.question_id AND q.stats
            GROUP BY e.question_id
            ORDER BY percentage_error""")
        result_list = []
        for row in cursor.fetchall():
            question = Question.objects.get(pk=row[0])
            #percentage_error = 100 * math.fabs(question.answer - row[1]) / question.answer
            s = self.model(user=User(), question=question, estimate=row[1], score=row[2], percentage_error=row[3])
            result_list.append(s)
        return result_list
    
    def get_avg_estimate(self, question):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT AVG(e.estimate) as estimate, AVG(e.score) as score 
            FROM questions_estimate e
            WHERE e.question_id == """+str(question.id)+"""
            GROUP BY e.question_id""")
        result = None
        row = cursor.fetchone()
        if row:
            percentage_error = 100 * math.fabs(question.answer - row[0]) / question.answer
            result = self.model(user=User(), question=question, estimate=row[0], score=row[1], percentage_error=percentage_error)
        return result

    def get_best_estimates(self):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.question_id, e.user_id, e.estimate, e.score, MIN(e.percentage_error) as percentage_error
            FROM questions_estimate e
            GROUP BY e.question_id
            ORDER BY e.percentage_error""")
        result_list = []
        for row in cursor.fetchall():
            question = Question.objects.get(pk=row[0])
            user = User.objects.get(pk=row[1])
            s = self.model(user=user, question=question, estimate=row[2], score=row[3], percentage_error=row[4])
            result_list.append(s)
        return result_list

    def get_best_estimate(self, question):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id, e.estimate, e.score, MIN(e.percentage_error) as percentage_error
            FROM questions_estimate e
            WHERE e.question_id == """+str(question.id))
        result = None
        row = cursor.fetchone()
        if row:
            user = User.objects.get(pk=row[0])
            result = self.model(user=user, question=question, estimate=row[1], score=row[2], percentage_error=row[3])
        return result

class Estimate(models.Model):
    """Estimate model."""
    user = models.ForeignKey(to=User, verbose_name=u'Benutzer', help_text='Bitte den Benutzer auswählen, der die diese Schätzung abgibt.')
    question = models.ForeignKey(to=Question, related_name='estimates', verbose_name=u'Frage', help_text='Bitte die Frage auswählen, zu der diese Schätzung gehören soll.')
    estimate = models.FloatField(verbose_name=u'Schätzwert', unique=False, help_text="Bitte hier einen Schätzwert eintragen. (Nur numerische Werte sind möglich)", null=True, blank=True)
    percentage_error = models.FloatField(verbose_name=u'Prozentualer Fehler', null=True, blank=True)
    date = models.DateTimeField(verbose_name=u'Datum', null=True, blank=True)
    score = models.IntegerField(verbose_name=u'Punkte', null=True, blank=True)
    objects = EstimateManager()
    
    class Meta:
        verbose_name = u'Schätzung'
        verbose_name_plural = u'Schätzungen'
        ordering = ['-date']
        unique_together = ['date', 'user', 'question']

    def __unicode__(self):
        return unicode(self.user) + u': ' + unicode(self.estimate)

    def save(self, *args, **kwargs):
        if not self.id:
            self.date = now()
        self.percentage_error = self.calculate_percentage_error()
        self.score = self.calculate_score()
        super(Estimate, self).save(*args, **kwargs)
    
    def calculate_score(self):
        """
        Function calculates the score for this estimate
        """
        if self.estimate == None:
            # no estimate made because time limit reached
            score = 0
        else:
            percentage_error = self.percentage_error / 100
            percentage_error = min(percentage_error, 1)
            max_points = 100
            score = int(round(max_points * (1-percentage_error)))
            #score = min(max_points*(math.tanh(6*(1-percentage_error)-4)+1.1)/2,max_points)
            #score = round(57.9073*math.exp(1-percentage_error) - 57.4083)
        return score
    
    def update_score(self):
        self.score = self.calculate_score()
        self.save()

    def calculate_percentage_error(self):
        if self.estimate == None:
            return None
        percentage_error = math.fabs((self.question.answer - self.estimate) / self.question.answer) * 100
        return percentage_error

    def update_percentage_error(self):
        self.percentage_error = self.calculate_percentage_error()
        self.save()


# =============================================================================
# CHALLENGE MODEL
# =============================================================================
class Challenge(models.Model):
    """Challenge model."""
    title = models.CharField(u'Titel', max_length=100, help_text="Bitte einen Titel für die Challenge eingeben (mit max. 100 Zeichen).")
    questions = models.ManyToManyField(Question, verbose_name=u'Fragen', help_text="Bitte hier die Schätz-Fragen auswählen.")
    published = models.BooleanField(verbose_name=u'Veröffentlicht', default=True,  help_text='Challenge zur Verfügung stellen?')
    author = models.ForeignKey(User, verbose_name=u'Autor')
    slug = models.SlugField(unique=True)
    date_created = models.DateTimeField(editable=False, verbose_name=u'Erstellt')
    date_updated = models.DateTimeField(editable=False, verbose_name=u'Zuletzt Geändert')
    
    class Meta:
        verbose_name = u'Challenge'
        verbose_name_plural = u'Challenges'
        ordering = ['-date_created']

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.id:
            self.date_created = now()
        self.date_updated = now()
        super(Challenge, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('questions_challenge_show', (), {'slug': self.slug})



# =============================================================================
# SCORE MODEL
# =============================================================================
class ScoreManager(models.Manager):
    def get_highscore(self):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, SUM(e.score) as score
            FROM questions_estimate e
            GROUP BY e.user_id
            ORDER BY score DESC
            LIMIT 0, 25""")
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1])
            result_list.append(s)
        return result_list

class Score(models.Model):
    user = models.ForeignKey(to=User, verbose_name=u'Benutzer')
    score = models.IntegerField(verbose_name=u'Punkte')
    objects = ScoreManager()

