#!/usr/bin/env python
# coding: utf8

#from django.shortcuts import render
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.db.models import Min
from django.utils.timezone import now
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.core.mail import mail_admins
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import datetime

from questions.forms import EstimateForm, QuestionForm, UserProfileForm, FeedbackForm, FeedbackQuestionForm
from questions.models import Question, Estimate, Score, Challenge, QuestionView
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login
from userauth.forms import UserCreationFormCustom
import logging
import random

logger = logging.getLogger('estimate.questions.views')


def menu_view(request):
    """
    Shows a menu
    """
    # read cookie
    guest_id = request.COOKIES.get('estimate_guest_id')
    logger.debug(guest_id)

    if request.user.is_authenticated():
        if request.user.is_active and request.user.is_superuser:
            is_admin = True
        else:
            is_admin = False

        challenges = Challenge.objects.filter(published=True)
        if len(challenges) == 0:
            challenges = None

        estimates = Estimate.objects.filter(user=request.user).exclude(estimate=None).order_by('percentage_error')
        
        score = 0
        for e in estimates:
            score += e.score

        number_estimates = len(estimates)
        
        return render_to_response('questions/menu.html', {'user': request.user, 'is_admin': is_admin, 'challenges': challenges, 'score': score, 'number_estimates': number_estimates}, context_instance=RequestContext(request))
    else:
        login_form = AuthenticationForm()
        questions = Question.objects.filter(published=True)
        question = random.choice(questions)

        if request.method == 'POST':
            register_form = UserCreationFormCustom(request.POST)
            if register_form.is_valid():
                username = request.POST[u'username']
                pwd = request.POST[u'password1']

                # check if user already answered questions as guest
                user = None
                if guest_id:
                    users = User.objects.filter(id=guest_id)
                    if users:
                        user = users[0]

                if user:
                    user.username = username
                    user.set_password(pwd)
                    user.save()
                    logger.debug(user)
                    new_user = authenticate(username=username, password=pwd)
                    login(request, new_user)
                else:
                    register_form.save()
                    new_user = authenticate(username=username, password=pwd)
                    login(request, new_user)

                response = HttpResponseRedirect('willkommen/')
                response.delete_cookie('estimate_guest_id')
                return response
        else:
            register_form = UserCreationFormCustom()
        return render_to_response('questions/landing-page.html', {'form': login_form, 'register_form': register_form, 'question': question},
            context_instance=RequestContext(request))
        
@login_required
def questions_list_all(request):
    """
    List all Questions
    """
    questions = Question.objects.filter(published=True)
    if not questions:
        title = u'Keine Frage verfügbar'
        message = u'Sorry ' + request.user.username + u', es stehen momentan leider keine Fragen zur Verfügung.'
        return render(request, 'questions/message.html', {'title': title, 'message': message})

    # filter out own questions
    questions = questions.exclude(author=request.user)
    
    # filter out questions, which were already answered
    estimates = Estimate.objects.filter(user=request.user)
    ready_questions = []
    time_out = []
    for e in estimates:
        questions = questions.exclude(pk=e.question.pk)
        if e.time_out:
            time_out.append(e.question)
        else:
            ready_questions.append(e.question)

    own_questions = Question.objects.filter(published=True, author=request.user)

    return render_to_response('questions/questions-list-all.html', {'question_list': questions, 'ready_list': ready_questions, 'time_out': time_out, 'own_questions': own_questions, 'user': request.user}, context_instance=RequestContext(request))


@login_required
def question_view(request, slug):
    """
    Show a question with estimate form or reached score
    """
    if request.user.is_authenticated():
        if request.user.is_active and request.user.is_superuser:
            is_admin = True
        else:
            is_admin = False

    question = get_object_or_404(Question, slug=slug, published=True)
    estimates = Estimate.objects.filter(question=question, user=request.user)
    
    # for this questions does already exist an estimate from the current user
    if estimates and not is_admin:
        estimate = estimates[0]
        next_random = False
        return render(request, 'questions/question-score.html',
            {'question': question, 'estimate': estimate, 'next_random': next_random})
    
    # current user hasn't already made an estimate for this question
    if request.method == 'POST':
        time_out = False

        # get hidden post field
        if request.POST.get("time_out", "") == "true":
            time_out = True

        form = EstimateForm(user=request.user, question=question, time_out=time_out, data=request.POST)
        if form.is_valid():
            if not is_admin:
                form.save()
                views = QuestionView.objects.filter(user=request.user, question=question)
                if views:
                    # delete saved view timestamps
                    views.delete()

            return HttpResponseRedirect(question.get_absolute_url())
    else:
        time_max = 40
        form = EstimateForm()
        views = QuestionView.objects.filter(user=request.user, question=question)
        if views:
            # question was already viewed before
            time = views[0].time
            current_time = now()
            timediff = current_time - time
            seconds = int(timediff.total_seconds())
            time_left = max(0, time_max - seconds)

            if time_left == 0:
                # no time left
                too_late = Estimate(user=request.user, question=question, time_out=True)
                too_late.save()
                views.delete()
                return HttpResponseRedirect(question.get_absolute_url())
        else:
            # question view for first time
            view = QuestionView(user=request.user, question=question)
            view.save()
            time_left = time_max
    return render(request, 'questions/question-show.html',
        {'form': form, 'question': question, 'user': request.user, 'time_left': time_left})


@login_required
def question_view_random(request, slug):
    """
    Show a randomly chosen question with estimate form or reached score
    """
    if request.user.is_authenticated():
        if request.user.is_active and request.user.is_superuser:
            is_admin = True
        else:
            is_admin = False

    question = get_object_or_404(Question, slug=slug, published=True)
    estimates = Estimate.objects.filter(question=question, user=request.user)
    
    # for this questions does already exist an estimate from the current user
    if estimates and not is_admin:
        estimate = estimates[0]
        next_random = True
        return render(request, 'questions/question-score.html',
            {'question': question, 'estimate': estimate, 'next_random': next_random})
    
    # current user hasn't already made an estimate for this question
    if request.method == 'POST':
        time_out = False

        # get hidden post field
        if request.POST.get("time_out", "") == "true":
            time_out = True

        form = EstimateForm(user=request.user, question=question, time_out=time_out, data=request.POST)
        if form.is_valid():
            if not is_admin:
                form.save()
                views = QuestionView.objects.filter(user=request.user, question=question)
                if views:
                    # delete saved view timestamps
                    views.delete()

            return HttpResponseRedirect("/zufall/"+question.slug)
    else:
        time_max = 40
        form = EstimateForm()
        views = QuestionView.objects.filter(user=request.user, question=question)
        if views:
            # question was already viewed before
            time = views[0].time
            current_time = now()
            timediff = current_time - time
            seconds = int(timediff.total_seconds())
            time_left = max(0, time_max - seconds)

            if time_left == 0:
                # no time left
                too_late = Estimate(user=request.user, question=question, time_out=True)
                too_late.save()
                views.delete()
                return HttpResponseRedirect("/zufall")
        else:
            # question view for first time
            view = QuestionView(user=request.user, question=question)
            view.save()
            time_left = time_max
    return render(request, 'questions/question-show.html',
        {'form': form, 'question': question, 'user': request.user, 'time_left': time_left})

@login_required
def question_random(request):
    """
    Show a random question, which were not answered before
    """
    questions = Question.objects.filter(published=True).exclude(author=request.user)
    if not questions:
        title = u'Keine Frage verfügbar'
        message = u'Sorry ' + request.user.username + u', es stehen momentan leider keine Fragen zur Verfügung.'
        return render(request, 'questions/message.html', {'title': title, 'message': message})

    # filter out questions, which were already answered
    estimates = Estimate.objects.filter(user=request.user)
    for e in estimates:
        questions = questions.exclude(pk=e.question.pk)
    
    if questions.count() == 0:
        # there are no unanswered questions left
        title = u'Alle Fragen beantwortet'
        message = u'Glückwunsch, du hast alle Fragen beantwortet. Momentan stehen leider keine weiteren Fragen zur Verfügung. Willst du das ändern? Dann überlege dir doch mal weitere Fragen.'
        return render(request, 'questions/message.html', {'title': title, 'message': message})
    
    question = random.choice(questions)

    # get another questions for statistics, so that those questions are preferred
    questions_stats = questions.filter(stats=True)
    if questions_stats.count() > 0:
        question_stats = random.choice(questions_stats)
        # make a list of both selected questions and choose randomly one of them
        both_questions = [question_stats, question]
        question = random.choice(both_questions)

    return HttpResponseRedirect("/zufall/"+question.slug)


def question_start(request):
    """
    Show selected questions without login necessary.
    """
    questions = Question.objects.filter(published=True, stats=True)
    if not questions:
        title = u'Keine Frage verfügbar'
        message = u'Sorry ' + request.user.username + u', es stehen momentan leider keine Fragen zur Verfügung.'
        return render(request, 'questions/message.html', {'title': title, 'message': message})

    user = User()
    # read cookie
    guest_id = request.COOKIES.get('estimate_guest_id')

    if guest_id != 'None':
        # get guest user
        users = User.objects.filter(id=guest_id)
        if users:
            user = users[0]

    # new user registration
    if request.method == 'POST':
        register_form = UserCreationFormCustom(request.POST)
        if register_form.is_valid():
            username = request.POST[u'username']
            pwd = request.POST[u'password1']

            if user:
                user.username = username
                user.set_password(pwd)
                user.save()
                logger.debug(user)
                new_user = authenticate(username=username, password=pwd)
                login(request, new_user)
            else:
                register_form.save()
                new_user = authenticate(username=username, password=pwd)
                login(request, new_user)

            response = HttpResponseRedirect('willkommen/')
            response.delete_cookie('estimate_guest_id')
            return response

    # filter out questions, which were already answered
    estimates = Estimate.objects.filter(user=user)
    for e in estimates:
        questions = questions.exclude(pk=e.question.pk)
    
    if questions.count() == 0:
        # there are no unanswered questions left
        register_form = UserCreationFormCustom()

        # calculate the users score
        estimates = Estimate.objects.filter(user=user).exclude(estimate=None).order_by('percentage_error')
        score = 0
        for e in estimates:
            score += e.score

        # users avg score
        avg_score = 0
        if len(estimates) > 0:
            avg_score = score / len(estimates)

        response = render(request, 'questions/question-start-done.html', {'register_form': register_form, 'score': score, 'avg_score': avg_score})
    else:
        # choose a random question
        question = random.choice(questions)
        response = HttpResponseRedirect("/start/"+question.slug)

    if not guest_id:
        # set cookie with guest id
        set_cookie(response, 'estimate_guest_id', user.id, 1)

    return response


def question_view_start(request, slug):
    """
    Show a randomly chosen question with estimate form or reached score
    """
    question = get_object_or_404(Question, slug=slug, published=True)

    user = None

    # read cookie
    guest_id = request.COOKIES.get('estimate_guest_id')

    if guest_id != 'None':
        # get guest user
        users = User.objects.filter(id=guest_id)
        if users:
            user = users[0]

        # already made estimate? 
        estimates = Estimate.objects.filter(question=question, user=user)
        if estimates:
            # for this questions does already exist an estimate from the current user
            # show score for this question
            estimate = estimates[0]
            next_start = True
            response = render(request, 'questions/question-score.html',
                {'question': question, 'estimate': estimate, 'next_start': next_start})

            # set cookie with guest id
            set_cookie(response, 'estimate_guest_id', user.id, 1) 
            return response
    

    # no estimate from this user for this question
    if request.method == 'POST':
        time_out = False

        # get hidden post field
        if request.POST.get("time_out", "") == "true":
            time_out = True

        if not user:
            # new User has to be created
            username = 'gast'
            user = User(username=username)
            user.save()
            user.username = username + '-' + str(user.id)
            user.save()

        form = EstimateForm(user=user, question=question, time_out=time_out, data=request.POST)
        if form.is_valid():
            form.save()

            views = QuestionView.objects.filter(user=user, question=question)
            if views:
                # delete saved view timestamps
                views.delete()

            response = HttpResponseRedirect("/start/"+question.slug)

            # set cookie with guest id
            set_cookie(response, 'estimate_guest_id', user.id, 1)
    else:
        form = EstimateForm()
        time_max = 40

        views = None
        if user:
            views = QuestionView.objects.filter(user=user, question=question)

        if views:
            # question was already viewed before
            time = views[0].time
            current_time = now()
            timediff = current_time - time
            seconds = int(timediff.total_seconds())
            time_left = max(0, time_max - seconds)

            if time_left == 0:
                # no time left
                too_late = Estimate(user=user, question=question, time_out=True)
                too_late.save()
                views.delete()
                return HttpResponseRedirect("/start")
        else:
            # question view for first time
            if user:
                view = QuestionView(user=user, question=question)
                view.save()
            time_left = time_max

        response = render(request, 'questions/question-show.html',
            {'form': form, 'question': question, 'user': None, 'time_left': time_left})

    if user:
        # set cookie with guest id
        set_cookie(response, 'estimate_guest_id', user.id, 1)

    return response



@login_required
def question_create_view(request):
    """
    Show from for sending in a question
    """
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            question_title = form.cleaned_data['title']
            question = get_object_or_404(Question, title=question_title, author=request.user)
            return render(request, 'questions/question-create.html',
                {'form': None, 'question': question})
    else:
        form = QuestionForm()
    return render(request, 'questions/question-create.html',
        {'form': form})

@login_required
def challenges_list_all(request):
    challenges = Challenge.objects.filter(published=True)

    if len(challenges) == 0:
        title = u'Keine Challenge verfügbar'
        message = u'Sorry ' + request.user.username + u', es stehen momentan keine Challenges zur Verfügung.'
        return render(request, 'questions/message.html', {'title': title, 'message': message})

    completed_challenges = Challenge.objects.completed_challenges(request.user)
    if completed_challenges:
        score_list = []
        for c in completed_challenges:
            score_list.append(Score.objects.challenge_score(request.user, c))
        completed_challenges = zip(completed_challenges, score_list)

    incompleted_challenges = Challenge.objects.incompleted_challenges(request.user)
    if incompleted_challenges:
        left_questions_list = []
        status_list = []
        for c in incompleted_challenges:
            chall_questions = c.questions.exclude(author=request.user)
            answered_questions = Estimate.objects.number_answered_questions(request.user, c)
            left_questions = chall_questions.count() - answered_questions
            left_questions_list.append(left_questions)
            status = 100*answered_questions / chall_questions.count()
            status_list.append(status)
        incompleted_challenges = zip(incompleted_challenges, left_questions_list, status_list)

    own_challenges = Challenge.objects.own_challenges(request.user)

    open_questions = len(Question.objects.filter(published=True).exclude(author=request.user)) - len(Estimate.objects.filter(user=request.user))
    if open_questions <= 0:
        open_questions = None

    return render(request, 'questions/challenges-list-all.html', {'incompleted_challenges': incompleted_challenges, 'completed_challenges': completed_challenges, 'own_challenges': own_challenges, 'open_questions': open_questions})


@login_required
def challenge_view(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug, published=True)
    questions = challenge.questions.filter(published=True).exclude(author=request.user)
    own_questions = challenge.questions.filter(author=request.user)

    if len(questions) == 0 and len(own_questions) == 0:
        # give 404, if challenge has no published questions
        raise Http404

    # check for each question, if there is already an estimate
    estimates = []
    score = 0
    for q in questions:
        estimate = Estimate.objects.filter(question=q, user=request.user)
        if not estimate:
            # unanswered question found
            return HttpResponseRedirect("/challenge/"+slug+"/"+q.slug)

        challenge_estimate = estimate.filter(challenge=challenge)
        if challenge_estimate:
            estimates.append(challenge_estimate[0])
            score += challenge_estimate[0].score
        else:
            estimates.append(estimate[0])
            score += estimate[0].score

    if questions.count() > 0:
        score_per_question = score / questions.count()
    else: 
        score_per_question = 0

    # all questions already answered -> show result
    return render(request, 'questions/challenge-score.html',
        {'challenge': challenge, 'estimate_list': estimates, 'score': score, 'score_per_question': score_per_question, 'own_questions': own_questions})


@login_required
def challenge_question_view(request, challenge, question):
    challenge = get_object_or_404(Challenge, slug=challenge, published=True)
    question = get_object_or_404(Question, slug=question, published=True)

    questions = challenge.questions.filter(published=True)

    if len(questions) == 0:
        # give 404, if challenge has no published questions
        raise Http404

    if not question in questions:
        # give 404, if question is not in challenge
        raise Http404

    if request.user.is_authenticated():
        if request.user.is_active and request.user.is_superuser:
            is_admin = True
        else:
            is_admin = False

    all_questions = challenge.questions.exclude(author=request.user).count()
    answered_questions = Estimate.objects.number_answered_questions(request.user, challenge)
    current_question = answered_questions + 1

    estimates = Estimate.objects.filter(question=question, user=request.user)

    # for this questions does already exist an estimate from the current user
    if estimates and not is_admin:
        # redirect to result page
        estimate = estimates[0]
        return render(request, 'questions/question-score-challenge.html',
            {'question': question, 'estimate': estimate, 'challenge': challenge, 'all_questions': all_questions, 'answered_questions': answered_questions})

    if request.method == 'POST':
        time_out = False

        # get hidden post field
        if request.POST.get("time_out", "") == "true":
            time_out = True

        form = EstimateForm(user=request.user, question=question, time_out=time_out, data=request.POST, challenge=challenge)
        if form.is_valid():
            if not is_admin:
                form.save()
                views = QuestionView.objects.filter(user=request.user, question=question)
                if views:
                    # delete saved view timestamps
                    views.delete()

                for q in questions:
                    estimates = Estimate.objects.filter(question=q, user=request.user)
                    return HttpResponseRedirect(question.get_absolute_url_challenge(challenge.slug))

                    if len(estimates) == 0 and q != question and q.author != request.user:
                        # redirect to next unsanswered question
                        return HttpResponseRedirect("/challenge/"+challenge.slug+"/"+q.slug)
                # all questions answered -> redirect to result page
                return HttpResponseRedirect("/challenge/"+challenge.slug)
    else:
        time_max = 40
        form = EstimateForm()
        views = QuestionView.objects.filter(user=request.user, question=question)
        if views:
            # question was already viewed before
            time = views[0].time
            current_time = now()
            timediff = current_time - time
            seconds = int(timediff.total_seconds())
            time_left = max(0, time_max - seconds)

            if time_left == 0:
                # no time left
                too_late = Estimate(user=request.user, question=question, time_out=True, challenge=challenge)
                too_late.save()
                views.delete()
                # all questions answered -> redirect to result page
                return HttpResponseRedirect("/challenge/"+challenge.slug)
        else:
            # question view for first time
            view = QuestionView(user=request.user, question=question)
            view.save()
            time_left = time_max
    return render(request, 'questions/question-show.html',
        {'form': form, 'question': question, 'user': request.user, 'challenge': challenge, 'all_questions': all_questions, 'current_question': current_question, 'time_left': time_left})


@login_required
def statistics_crowd(request):
    """
    Show overall crowd statistics  
    """
    admin = False
    if request.user.is_active and request.user.is_superuser:
        admin = True        

    avg_percentage_error = 0

    avg_estimates = Estimate.objects.get_avg_estimates(admin)
    best_estimates = []
    count_estimates = []
    show_estimate = []

    for e in avg_estimates:
        avg_percentage_error += e.percentage_error
        best_estimate = Estimate.objects.filter(question=e.question, time_out=False).order_by('percentage_error')
        if best_estimate:
            best_estimates.append(best_estimate[0])
        else:
            best_estimates.append(None)

        count = Estimate.objects.filter(question=e.question).count()
        count_estimates.append(count)

        show = Estimate.objects.filter(question=e.question, user=request.user).exists() or e.question.author == request.user
        show_estimate.append(show)

    if len(avg_estimates) > 0:
        avg_percentage_error = avg_percentage_error / len(avg_estimates)

    best_avg_estimate = Estimate.objects.get_best_avg_estimate(admin)

    estimate_list = zip(avg_estimates, best_estimates, count_estimates, show_estimate)
    return render(request, 'questions/statistics-all.html', {'user': request.user, 'avg_percentage_error': avg_percentage_error, 'best_avg_estimate': best_avg_estimate, 'estimate_list': estimate_list})

@login_required
def question_statistics(request, slug):
    """
    Show statistics for given question
    """
    question = get_object_or_404(Question, slug=slug, published=True)

    admin = False
    if request.user.is_active and request.user.is_superuser:
        admin = True 

    if request.method == 'POST':
        if admin:
            estimate_id = request.POST.get('estimate_id')
            change_estimate = get_object_or_404(Estimate, id=estimate_id)

            if change_estimate.stats == True:
                change_estimate.stats = False
            else:
                change_estimate.stats = True
            
            change_estimate.save()
    
    estimates = Estimate.objects.filter(question=question).exclude(estimate=None).order_by('percentage_error')

    own_estimate_list = Estimate.objects.filter(user=request.user, question=question)
    if len(own_estimate_list) > 0:
        own_estimate = own_estimate_list[0]
    else:
        own_estimate = None

    # get the average estimate for this question
    avg_estimate = Estimate.objects.get_avg_estimate(question, admin)

    return render(request, 'questions/statistics-question.html', {'question': question, 'user':request.user, 'admin': admin, 'own_estimate': own_estimate, 'estimate_list': estimates, 'avg_estimate': avg_estimate})

@login_required
def statistics_user(request, user_id):
    """
    Show statistics for current user 
    """
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser and not request.user.is_superuser:
        raise Http404

    estimates = Estimate.objects.filter(user=user).exclude(time_out=True).exclude(estimate=None).order_by('percentage_error')
    estimates_time_out = Estimate.objects.filter(user=user, time_out=True)
    own_questions = Question.objects.filter(author=user, published=True)
    
    score = 0
    score_per_question = 0
    sum_percentage_error = 0
    error_per_question = 0

    if estimates.count() == 0:
        estimates = None
        return render(request, 'questions/statistics-user.html', {'user': request.user, 'show_user': user, 'score': score, 'estimate_list': estimates, 'estimates_time_out': estimates_time_out, 'score_per_question': score_per_question, 'error_per_question': error_per_question, 'own_questions': own_questions})
    else:
        show_estimate = []
        for e in estimates:
            score += e.score
            sum_percentage_error += e.percentage_error

            show = Estimate.objects.filter(question=e.question, user=request.user).exists() or e.question.author == request.user
            show_estimate.append(show)
        
        score_per_question = score / estimates.count()
        error_per_question = sum_percentage_error / estimates.count()

        estimates = zip(estimates, show_estimate)
        
        return render(request, 'questions/statistics-user.html', {'user': request.user, 'show_user': user, 'score': score, 'estimate_list': estimates, 'estimates_time_out': estimates_time_out, 'score_per_question': score_per_question, 'error_per_question': error_per_question, 'own_questions': own_questions})


@login_required
def account_settings(request):
    if request.method == "POST":
        user_form = UserProfileForm(data=request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
    pw_form = PasswordChangeForm(user=request.user)
    user_form = UserProfileForm(instance=request.user)
    return render(request, 'questions/account-settings.html', {'pw_form': pw_form, 'user_form': user_form, 'user': request.user})



@login_required
def question_highscore(request):
    """
    Show a highscore
    """
    scores = Score.objects.get_highscore(100)
    
    scores_per_question = Score.objects.get_highscore_per_question(100)
    
    scores_best_question = Score.objects.get_highscore_best_question(100)
    best_estimates = []
    for s in scores_best_question:
        estimate = Estimate.objects.filter(user=s.user, percentage_error=s.score)
        if estimate:
            best_estimates.append(estimate[0])
        else:
            best_estimates.append(None)

    best_estimates = zip(scores_best_question, best_estimates)

    scores_best_percentage_error = Score.objects.get_highscore_best_percentage_error(100)
    
    return render(request, 'questions/highscore.html', {'user': request.user, 'score_list': scores, 'per_question': scores_per_question, 'best_estimates': best_estimates, 'best_percentage_error': scores_best_percentage_error})


@login_required
def challenge_highscore(request, slug):
    """
    Show highscore for a given challenge
    """
    challenge = get_object_or_404(Challenge, slug=slug, published=True)
    own_questions = challenge.questions.filter(author=request.user)

    own_challenge = len(own_questions) == len(challenge.questions.all())

    if own_challenge:
        # all questions are from current user
        scores = Score.objects.challenge_highscore_all(challenge)
    else: 
        scores = Score.objects.challenge_highscore(challenge, request.user)

    return render(request, 'questions/challenge-highscore.html', {'user': request.user, 'challenge': challenge, 'score_list': scores, 'own_questions': own_questions, 'own_challenge': own_challenge})


def feedback(request):
    """ Send Feedback Mail. """
    if request.method == 'POST':
        email = request.POST[u'email']
        message = request.POST[u'message']
        name = request.POST[u'name']
        userid = request.POST[u'userid']
        questionid = request.POST.get(u'questionid')

        form = FeedbackForm()
        if questionid:
            form = FeedbackQuestionForm(request.POST)
        else:
            form = FeedbackForm(request.POST)

        if form.is_valid():
            form.save()
            return render_to_response('questions/message.html', {'title': 'Feedback gesendet', 'message': '<i class="fa feedback-sent-icon fa-5x fa-check-circle"></i> <p class="centered-text">Vielen Dank für dein Feedback!</p>'}, context_instance=RequestContext(request))

    else:
        form = FeedbackForm(initial={'name': request.user.username, 'email': request.user.email, 'userid': request.user.id})
    
    return render_to_response('questions/feedback.html', {'form': form}, context_instance=RequestContext(request))


def set_cookie(response, key, value, days_expire = 7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  #one year
    else:
        max_age = days_expire * 24 * 60 * 60 
        expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
        response.set_cookie(key, value, max_age=max_age, expires=expires, domain=settings.SESSION_COOKIE_DOMAIN, secure=settings.SESSION_COOKIE_SECURE or None)

