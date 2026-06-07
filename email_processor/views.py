from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Keyword
from gmail_sync.models import Email


@login_required
def keyword_list(request):
    keywords = Keyword.objects.filter(user=request.user)
    return render(request, 'keywords/list.html', {'keywords': keywords})


@login_required
@require_http_methods(['POST'])
def keyword_add(request):
    word = request.POST.get('keyword', '').strip()
    if word:
        Keyword.objects.get_or_create(user=request.user, keyword=word)
    return redirect('keywords:list')


@login_required
@require_http_methods(['POST'])
def keyword_toggle(request, pk):
    kw = get_object_or_404(Keyword, pk=pk, user=request.user)
    kw.enabled = not kw.enabled
    kw.save()
    return redirect('keywords:list')


@login_required
@require_http_methods(['POST'])
def keyword_delete(request, pk):
    Keyword.objects.filter(pk=pk, user=request.user).delete()
    return redirect('keywords:list')


@login_required
def email_list(request):
    qs = Email.objects.filter(user=request.user).select_related('analysis')
    category = request.GET.get('category')
    priority = request.GET.get('priority')
    search = request.GET.get('q')
    date_from = request.GET.get('date_from')

    if category:
        qs = qs.filter(analysis__category=category)
    if priority:
        qs = qs.filter(analysis__priority=priority)
    if search:
        qs = qs.filter(subject__icontains=search) | qs.filter(
            sender__icontains=search) | qs.filter(body__icontains=search)
    if date_from:
        qs = qs.filter(received_at__date__gte=date_from)

    return render(request, 'emails/list.html', {
        'emails': qs[:100],
        'category': category,
        'priority': priority,
        'search': search,
    })


@login_required
def email_detail(request, pk):
    email = get_object_or_404(Email, pk=pk, user=request.user)
    analysis = getattr(email, 'analysis', None)
    return render(request, 'emails/detail.html', {
        'email': email,
        'analysis': analysis,
    })