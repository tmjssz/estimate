#!/usr/bin/env python
# coding: utf8

#from django.shortcuts import render
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.shortcuts import render

from questions.forms import EstimateForm
from questions.models import Question, Estimate, Score, Challenge
from django.contrib.auth.models import User
import logging
import random

logger = logging.getLogger('estimate.questions.views')


def menu_view(request):
    """
    Shows a menu
    """
    if request.user.is_authenticated():
        if request.user.is_active and request.user.is_superuser:
            is_admin = True
        else:
            is_admin = False

        challenges = Challenge.objects.filter(published=True)
        if len(challenges) == 0:
            challenges = None
        
        return render_to_response('questions/menu.html', {'user': request.user, 'is_admin': is_admin, 'challenges': challenges}, context_instance=RequestContext(request))
    else:
        return render_to_response('questions/landing-page.html', context_instance=RequestContext(request))

def questions_list_all(request):
    """
    List all Questions
    """
    questions = Question.objects.filter(published=True)
    return render_to_response('questions/questions-list-all.html', {'object_list': questions}, context_instance=RequestContext(request))


@login_required
def question_view(request, slug):
    """
    Show a question with estimate form or reached score
    """
    question = get_object_or_404(Question, slug=slug, published=True)
    
    estimates = Estimate.objects.filter(question=question, user=request.user)
    
    # for this questions does already exist an estimate from the current user
    if estimates:
        estimate = estimates[0]
        avg_estimate = Estimate.objects.get_avg_estimate(question=question)
        return render(request, 'questions/question-score.html',
            {'question': question, 'estimate': estimate, 'avg_estimate': avg_estimate})
    
    # current user hasn't already made an estimate for this question
    if request.method == 'POST':
        form = EstimateForm(user=request.user, question=question, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(question.get_absolute_url())
    else:
        form = EstimateForm()
    return render(request, 'questions/question-show.html',
        {'form': form, 'question': question})


@login_required
def question_view_random(request):
    """
    Show a random question, which were not answered before
    """
    questions = Question.objects.filter(published=True)
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
        message = u'Sorry ' + request.user.username + u', du hast bereits zu jeder Frage eine Schätzung abgegeben. Leider stehen momentan keine weiteren Fragen zur Verfügung.'
        return render(request, 'questions/message.html', {'title': title, 'message': message})
    
    question = random.choice(questions)

    return HttpResponseRedirect("/frage/"+question.slug)


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
        status_list = []
        for c in incompleted_challenges:
            status_list.append(Estimate.objects.get_challenge_status(request.user, c))
        incompleted_challenges = zip(incompleted_challenges, status_list)

    return render(request, 'questions/challenges-list-all.html', {'incompleted_challenges': incompleted_challenges, 'completed_challenges': completed_challenges})


@login_required
def challenge_view(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug, published=True)
    questions = challenge.questions.filter(published=True)

    if len(questions) == 0:
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

    # all questions already answered -> show result
    return render(request, 'questions/challenge-score.html',
        {'challenge': challenge, 'estimate_list': estimates, 'score': score})


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

    if request.method == 'POST':
        form = EstimateForm(user=request.user, question=question, data=request.POST, challenge=challenge)
        if form.is_valid():
            form.save()
            for q in questions:
                estimates = Estimate.objects.filter(question=q, user=request.user)
                if len(estimates) == 0 and q != question:
                    # redirect to next unsanswered question
                    return HttpResponseRedirect("/challenge/"+challenge.slug+"/"+q.slug)
            # all questions answered -> redirect to result page
            return HttpResponseRedirect("/challenge/"+challenge.slug)
    else:
        form = EstimateForm()
    return render(request, 'questions/question-show.html',
       {'form': form, 'question': question})


@login_required
def statistics_all(request):
    """
    Show overall statistics  
    """
    if request.user.is_active and request.user.is_superuser:
        avg_percentage_error = 0

        avg_estimates = Estimate.objects.get_avg_estimates()
        best_estimates = []
        count_estimates = []

        for e in avg_estimates:
            avg_percentage_error += e.percentage_error
            best_estimate = Estimate.objects.get_best_estimate(e.question)
            best_estimates.append(best_estimate)
            count = Estimate.objects.filter(question=e.question).count()
            count_estimates.append(count)

        if len(avg_estimates) > 0:
            avg_percentage_error = avg_percentage_error / len(avg_estimates)

        #best_estimates = Estimate.objects.get_best_estimates()
        estimate_list = zip(avg_estimates, best_estimates, count_estimates)
        return render(request, 'questions/statistics-all.html', {'avg_percentage_error': avg_percentage_error, 'estimate_list': estimate_list})

    else:
        raise Http404

@login_required
def question_statistics(request, slug):
    """
    Show statistics for given question
    """
    question = get_object_or_404(Question, slug=slug, published=True)

    if request.user.is_active and request.user.is_superuser:
        admin = True
    else:
        admin = False
    
    estimates = Estimate.objects.filter(question=question).exclude(estimate=None).order_by('percentage_error')

    own_estimate_list = Estimate.objects.filter(user=request.user, question=question)
    if len(own_estimate_list) > 0:
        own_estimate = own_estimate_list[0]
    else:
        own_estimate = None

    return render(request, 'questions/statistics-question.html', {'question': question, 'user':request.user, 'admin': admin, 'own_estimate': own_estimate, 'estimate_list': estimates})


@login_required
def statistics_user(request, username):
    """
    Show statistics for a given user 
    """
    show_user = get_object_or_404(User, username=username)
    estimates = Estimate.objects.filter(user=show_user).exclude(estimate=None).order_by('percentage_error')
    estimates_time_out = Estimate.objects.filter(user=show_user, estimate=None)
    
    score = 0
    for e in estimates:
        score += e.score

    if estimates.count() == 0:
        estimates = None

    return render(request, 'questions/statistics-user.html', {'user': request.user, 'show_user': show_user, 'score': score, 'estimate_list': estimates, 'estimates_time_out': estimates_time_out})


@login_required
def question_highscore(request):
    """
    Show a highscore
    """
    scores = Score.objects.get_highscore()
    return render(request, 'questions/highscore.html', {'user': request.user, 'score_list': scores})


@login_required
def challenge_highscore(request, slug):
    """
    Show highscore for a given challenge
    """
    challenge = get_object_or_404(Challenge, slug=slug, published=True)
    scores = Score.objects.challenge_highscore(challenge)
    return render(request, 'questions/challenge-highscore.html', {'user': request.user, 'challenge': challenge, 'score_list': scores})
