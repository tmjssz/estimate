# encoding: utf-8
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from django.utils.html import urlize
import math
import logging

logger = logging.getLogger('estimate.questions.views')


# =============================================================================
# +++ QUESTION +++
# =============================================================================
class Question(models.Model):
    """Question model."""
    title = models.CharField(u'Titel', max_length=100, help_text="Bitte einen Titel für die Frage eingeben (mit max. 100 Zeichen).")
    question = models.TextField(u'Frage', help_text="Bitte hier die Schätz-Frage eingeben. Es sind nur Fragen mit numerischen Antworten erlaubt.")
    answer = models.FloatField(verbose_name=u'Antwort', help_text="Bitte hier eine gültige Antwort eingeben. (Nur numerische Werte sind möglich)")
    unit = models.CharField(u'Einheit', max_length=100, help_text="Hier kann angegeben werden in welcher Einheit der Schätzwert sein soll. (optional)", blank=True, null=True)
    explanation = models.TextField(u'Erklärung', help_text="Hier kann eine Erklärung oder ein Kommentar zur Auflösung eingetragen werden. (optional)", blank=True, null=True)
    source = models.CharField(u'Quelle', max_length=300, help_text="Bitte hier die Quelle für die oben angegebene Antwort eintragen. (beispielsweise die URL zu einer Webseite)", blank=True, null=True)
    image = models.ImageField(u'Bild', help_text='Hier kann ein Bild hochgeladen werden. (optional)', upload_to='media/', blank=True, null=True)
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
        self.source = urlize(self.source).replace('<a href="', '<a target="_blank" href="')

        super(Question, self).save(*args, **kwargs)
        
        estimates = Estimate.objects.filter(question=self.id)
        for e in estimates:
            e.update_percentage_error()
            e.update_score()

    @models.permalink
    def get_absolute_url(self):
        return ('questions_question_show', (), {'slug': self.slug})

    @models.permalink
    def get_absolute_url_random(self):
        return ('questions_question_random', (), {'slug': self.slug})

    @models.permalink
    def get_absolute_url_challenge(self, challenge):
        return ('questions_challenge_question_show', (), {'question': self.slug, 'challenge': challenge})



# =============================================================================
# +++ CHALLENGE +++
# =============================================================================
class ChallengeManager(models.Manager):

    def completed_challenges(self, user):
        """
        Returns a list of completed challenges for given user
        """
        completed = []
        challenges = Challenge.objects.filter(published=True)
        for c in challenges:
            answered = Estimate.objects.number_answered_questions(user, c)
            number_total = c.questions.exclude(author=user).count()
            if answered == number_total and number_total > 0:
                completed.append(c)

        if len(completed) == 0:
            return None
        
        return completed

    def incompleted_challenges(self, user):
        """
        Returns a list of not completed challenges for given user
        """
        incompleted = []
        challenges = Challenge.objects.filter(published=True)
        for c in challenges:
            answered = Estimate.objects.number_answered_questions(user, c)
            if answered < c.questions.exclude(author=user).count():
                incompleted.append(c)

        if len(incompleted) == 0:
            return None
        
        return incompleted

    def own_challenges(self, user):
        """
        Returns a list of challenges containing only questions created by given user
        """
        own = []
        challenges = Challenge.objects.filter(published=True)
        for c in challenges:
            if c.questions.exclude(author=user).count() == 0:
                own.append(c)

        if len(own) == 0:
            return None
        
        return own

# -----------------------------------------------------------------------------
# CHALLENGE MODEL
# -----------------------------------------------------------------------------
class Challenge(models.Model):
    """Challenge model."""
    title = models.CharField(u'Titel', max_length=100, help_text="Bitte einen Titel für die Challenge eingeben (mit max. 100 Zeichen).")
    questions = models.ManyToManyField(Question, verbose_name=u'Fragen', limit_choices_to={'published': True}, help_text="Bitte hier die Schätz-Fragen auswählen.")
    published = models.BooleanField(verbose_name=u'Veröffentlicht', default=True,  help_text='Challenge zur Verfügung stellen?')
    author = models.ForeignKey(User, verbose_name=u'Autor')
    slug = models.SlugField(unique=True)
    date_created = models.DateTimeField(editable=False, verbose_name=u'Erstellt')
    date_updated = models.DateTimeField(editable=False, verbose_name=u'Zuletzt Geändert')
    objects = ChallengeManager()
    
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
# +++ ESTIMATE +++
# =============================================================================
class EstimateManager(models.Manager):
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Statistics functions
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_avg_estimates(self, only_specified):
        from django.db import connection
        cursor = connection.cursor()

        stats = ''
        if only_specified:
            stats = 'AND q.stats'

        cursor.execute("""
            SELECT e.question_id, AVG(e.estimate) as estimate, AVG(e.score) as score, 100*ABS(q.answer-AVG(e.estimate))/q.answer as percentage_error 
            FROM questions_estimate e, questions_question q
            WHERE q.id = e.question_id """+stats+"""
            GROUP BY e.question_id
            ORDER BY percentage_error""")
        result_list = []
        for row in cursor.fetchall():
            question = Question.objects.get(pk=row[0])
            if not row[3]:
                if question.answer == 0:
                    percentage_error = math.fabs(row[1])
                else:
                    percentage_error = 100
            else:
                percentage_error = row[3]

            s = self.model(user=User(), question=question, estimate=row[1], score=row[2], percentage_error=percentage_error)
            result_list.append(s)
        return result_list
    
    def get_avg_estimate(self, question):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT AVG(e.estimate) as estimate, AVG(e.score) as score 
            FROM questions_estimate e
            WHERE e.question_id="""+str(question.id)+
            """ GROUP BY e.question_id""")
        result = None
        row = cursor.fetchone()
        if row:
            percentage_error = None
            if row[0]:
                if question.answer == 0:
                    # if question answer is zero
                    percentage_error = math.fabs(row[0])
                else:
                    percentage_error = 100 * math.fabs(question.answer - row[0]) / question.answer
            
            result = self.model(user=User(), question=question, estimate=row[0], score=row[1], percentage_error=percentage_error)
        return result

    def get_best_avg_estimate(self, only_specified):
        """
        Calculates for each user his personal average estimate from all his given estimates.
        Returns the best one.
        """
        from django.db import connection
        cursor = connection.cursor()

        stats = ''
        if only_specified:
            stats = 'AND q.stats'

        cursor.execute("""
            SELECT COUNT(*) as number
            FROM questions_estimate e, questions_question q
            WHERE e.question_id = q.id """+stats+"""
            GROUP BY e.user_id
            ORDER BY number DESC""")

        number_questions = 0
        row = cursor.fetchone()
        if row:
            number_questions = row[0]

        cursor.execute("""
            SELECT AVG(e.estimate) as estimate, e.user_id, AVG(e.score) as score, AVG(e.percentage_error) as percentage_error 
            FROM questions_estimate e, questions_question q
            WHERE q.id = e.question_id """+stats+"""
            GROUP BY e.user_id
            HAVING COUNT(*)>="""+str(number_questions)+"""
            ORDER BY percentage_error""")
        result = None
        row = cursor.fetchone()
        if row:
            user = User.objects.get(pk=row[1]) 
            question = Question()           
            result = self.model(user=user, question=question, estimate=row[0], score=row[2], percentage_error=row[3])
        return result


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Challenge's estimates
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def number_answered_questions(self, user, challenge):
        """
        Returns the number of how many questions are already answered for the given challenge
        """
        questions = challenge.questions.filter(published=True).exclude(author=user)
        counter = 0
        for q in questions:
            estimate = Estimate.objects.filter(question=q, user=user)
            if estimate:
                counter += 1
        return counter

# -----------------------------------------------------------------------------
# ESTIMATE MODEL
# -----------------------------------------------------------------------------
class Estimate(models.Model):
    """Estimate model."""
    user = models.ForeignKey(to=User, verbose_name=u'Benutzer', help_text='Bitte den Benutzer auswählen, der die diese Schätzung abgibt.')
    question = models.ForeignKey(to=Question, related_name='estimates', verbose_name=u'Frage', help_text='Bitte die Frage auswählen, zu der diese Schätzung gehören soll.')
    estimate = models.FloatField(verbose_name=u'Schätzwert', unique=False, help_text="Bitte hier einen Schätzwert eintragen. (Nur numerische Werte sind möglich)", null=True, blank=True)
    percentage_error = models.FloatField(verbose_name=u'Prozentualer Fehler', null=True, blank=True)
    time_out = models.BooleanField(verbose_name=u'Zeit abgelaufen', default=False)
    date = models.DateTimeField(verbose_name=u'Datum', null=True, blank=True)
    score = models.IntegerField(verbose_name=u'Punkte', null=True, blank=True)
    challenge = models.ForeignKey(Challenge, verbose_name=u'Challenge', help_text="Hier bitte auswählen, zu welcher Challenge die Schätzung abgegeben wird.", blank=True, null=True)
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
        
        if self.question.answer == 0:
            # if the question answer is zero
            percentage_error = math.fabs(self.estimate)
        else:
            percentage_error = math.fabs((self.question.answer - self.estimate) / self.question.answer) * 100
        return percentage_error

    def update_percentage_error(self):
        self.percentage_error = self.calculate_percentage_error()
        self.save()



# =============================================================================
# +++ SCORE +++
# =============================================================================
class ScoreManager(models.Manager):

    def get_highscore(self, limit):
        """
        Returns the score for every user.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, SUM(e.score) as score, COUNT(*) as number
            FROM questions_estimate e
            WHERE NOT e.time_out
            GROUP BY e.user_id
            ORDER BY score DESC
            LIMIT 0, """ + str(limit))
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

    def get_highscore_per_question(self, limit):
        """
        Returns the score for every user.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, SUM(e.score) / count(*) as score_per_question, COUNT(*) as number
            FROM questions_estimate e
            WHERE NOT e.time_out
            GROUP BY e.user_id
            ORDER BY score_per_question DESC
            LIMIT 0, """ + str(limit))
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

    def get_highscore_best_question(self, limit):
        """
        Returns the score for every user.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, MIN(e.percentage_error) as percentage_error, COUNT(*) as number
            FROM questions_estimate e
            WHERE NOT e.time_out
            GROUP BY e.user_id
            ORDER BY percentage_error ASC
            LIMIT 0, """ + str(limit))
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

    def get_highscore_best_percentage_error(self, limit):
        """
        Returns the score for every user.
        Ordered ascending by percentage error.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, AVG(e.percentage_error) as percentage_error, COUNT(*) as number
            FROM questions_estimate e
            WHERE NOT e.time_out
            GROUP BY e.user_id
            ORDER BY percentage_error
            LIMIT 0, """ + str(limit))
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Challenge's Scores
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def challenge_highscore_all(self, challenge):
        """
        Returns the challenge score for every user, who played a given challenge.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, SUM(e.score) as score
            FROM questions_estimate e, questions_challenge_questions q
            WHERE q.challenge_id = """+str(challenge.id)+""" 
                AND q.question_id = e.question_id 
            GROUP BY e.user_id
            HAVING COUNT(*) = """+str(len(challenge.questions.all()))+"""
            ORDER BY score DESC""")
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1])
            result_list.append(s)
        return result_list

    def challenge_highscore(self, challenge, user):
        """
        Returns the challenge score for every user, who played a given challenge.
        Does not take scores from estimates for questions, that were created by the given user.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, SUM(e.score) as score
            FROM questions_estimate e, questions_challenge_questions q, questions_question q1
            WHERE q.challenge_id = """+str(challenge.id)+""" 
                AND q.question_id = e.question_id 
                AND q1.id = q.question_id 
                AND q1.author_id <> """ + str(user.id) + """
            GROUP BY e.user_id
            HAVING COUNT(*) = """+str(len(challenge.questions.all().exclude(author=user)))+"""
            ORDER BY score DESC""")
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1])
            result_list.append(s)
        return result_list

    def challenge_score(self, user, challenge):
        """
        Returns a user's score for a given challenge.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT SUM(e.score) as score
            FROM questions_estimate e, questions_challenge_questions q
            WHERE q.challenge_id = """+str(challenge.id)+""" 
                AND q.question_id = e.question_id
                AND e.user_id = """+str(user.id))
        result = None
        row = cursor.fetchone()
        if row:
            result = self.model(user=user, score=row[0])
        return result

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Group's Scores
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def group_highscore(self, group):
        """
        Returns the group score for every user in the given group.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, SUM(e.score) as score, COUNT(*)
            FROM questions_estimate e, auth_user_groups a
            WHERE a.group_id = """+str(group.id)+"""
                AND a.user_id = e.user_id 
                AND NOT e.time_out
            GROUP BY e.user_id
            ORDER BY score DESC""")
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

    def get_highscore_per_question_group(self, group):
        """
        Returns the score for every user in a given group.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, SUM(e.score) / count(*) as score_per_question, COUNT(*) as number
            FROM questions_estimate e, auth_user_groups a
            WHERE a.group_id = """+str(group.id)+"""
                AND a.user_id = e.user_id
                AND NOT e.time_out
            GROUP BY e.user_id
            ORDER BY score_per_question DESC""")
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

    def get_highscore_best_question_group(self, group):
        """
        Returns the score for every user.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, MIN(e.percentage_error) as percentage_error, COUNT(*) as number
            FROM questions_estimate e, auth_user_groups a
            WHERE a.group_id = """+str(group.id)+"""
                AND a.user_id = e.user_id
                AND NOT e.time_out
            GROUP BY e.user_id
            ORDER BY percentage_error ASC""")
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

    def get_highscore_best_percentage_error_group(self, group):
        """
        Returns the score for every user.
        Ordered ascending by percentage error.
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT e.user_id as user, AVG(e.percentage_error) as percentage_error, COUNT(*) as number
            FROM questions_estimate e, auth_user_groups a
            WHERE a.group_id = """+str(group.id)+"""
                AND a.user_id = e.user_id
                AND NOT e.time_out
            GROUP BY e.user_id
            ORDER BY percentage_error""")
        result_list = []
        for row in cursor.fetchall():
            user = User.objects.get(pk=row[0])
            s = self.model(user=user, score=row[1], number=row[2])
            result_list.append(s)
        return result_list

# -----------------------------------------------------------------------------
# SCORE MODEL
# -----------------------------------------------------------------------------
class Score(models.Model):
    user = models.ForeignKey(to=User, verbose_name=u'Benutzer')
    score = models.IntegerField(verbose_name=u'Punkte')
    number = models.IntegerField(verbose_name=u'Anzahl')
    objects = ScoreManager()

    def __unicode__(self):
        if self.score == 1:
            return str(self.score) + u' Punkt'
        return str(self.score) + u' Punkte'

