import re
import time

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import linebreaks as _linebreaks
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm
from .models import Article, Category, Comment

_BLOCK_HTML_RE = re.compile(
    r'<\s*(/?\s*)(p|h[1-6]|ul|ol|li|div|blockquote|table|pre|section|figure|hr)\b', re.I)


def _article_content_html(content):
    """متن‌های HTML (تولیدشده با نوار ابزار مدیر) بدون linebreaks رندر می‌شوند —
    وگرنه هر خط‌تجدید داخل <ul>/<h2>… به <br> اضافه تبدیل می‌شد.
    برای متن‌های ساده (بدون تگ بلوکی) linebreaks اعمال می‌شود."""
    content = content or ''
    if _BLOCK_HTML_RE.search(content):
        return content
    return _linebreaks(content)

COMMENT_MIN_LEN = 3
COMMENT_MAX_LEN = 1000
COMMENT_COOLDOWN_SECONDS = 10
PAGE_SIZE = 9


def _published_articles():
    return (Article.objects
            .filter(published_at__lte=timezone.now(), is_published=True)
            .select_related('category')
            .annotate(comments_count=Count('comments', filter=Q(comments__is_approved=True))))


def _session_list(session, key):
    lst = session.get(key)
    if not isinstance(lst, list):
        lst = []
        session[key] = lst
    return lst


def blog_home(request):
    articles = _published_articles().order_by('-published_at')

    q = request.GET.get('q', '').strip()
    cat = request.GET.get('cat', '').strip()
    if q:
        articles = articles.filter(
            Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(content__icontains=q))
    active_category = None
    if cat:
        active_category = Category.objects.filter(slug=cat).first()
        if active_category:
            articles = articles.filter(category=active_category)

    paginator = Paginator(articles, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'articles': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'featured_articles': _published_articles().filter(is_featured=True)[:5],
        'popular_articles': _published_articles().order_by('-views')[:5],
        'categories': Category.objects.annotate(
            articles_count=Count('articles',
                                 filter=Q(articles__published_at__lte=timezone.now()))),
        'q': q,
        'active_category': active_category,
    }
    return render(request, 'blog.html', context)


def article_detail(request, article_id):
    article = get_object_or_404(_published_articles(), pk=article_id)

    Article.objects.filter(pk=article_id).update(views=F('views') + 1)
    article.views += 1

    comments = (article.comments
                .filter(parent__isnull=True, is_approved=True)
                .select_related('user')
                .prefetch_related('replies__user'))

    related = (_published_articles()
               .filter(category=article.category)
               .exclude(pk=article.pk))[:3]

    context = {
        'article': article,
        'content_html': _article_content_html(article.content),
        'comments': comments,
        'comments_count': article.comments.filter(is_approved=True).count(),
        'comment_form': CommentForm() if request.user.is_authenticated else None,
        'liked_comments': _session_list(request.session, 'liked_comments'),
        'article_liked': article_id in _session_list(request.session, 'liked_articles'),
        'related_articles': related,
    }
    return render(request, 'article_detail.html', context)


@require_POST
@login_required
def add_comment(request):
    form = CommentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'error': 'متن نظر معتبر نیست.'}, status=400)

    content = (form.cleaned_data.get('content') or '').strip()
    if len(content) < COMMENT_MIN_LEN:
        return JsonResponse({'success': False,
                             'error': f'نظر باید حداقل {COMMENT_MIN_LEN} حرف باشد.'}, status=400)
    if len(content) > COMMENT_MAX_LEN:
        return JsonResponse({'success': False,
                             'error': f'نظر نمی‌تواند بیش از {COMMENT_MAX_LEN} حرف باشد.'}, status=400)

    article = get_object_or_404(Article, pk=request.POST.get('article_id'),
                                published_at__lte=timezone.now(), is_published=True)

    parent = None
    parent_id = request.POST.get('parent_id')
    if parent_id and parent_id != 'null' and parent_id != '':
        parent = get_object_or_404(Comment, pk=parent_id)
        if parent.article_id != article.id:
            return JsonResponse({'success': False, 'error': 'پاسخ نامعتبر است.'}, status=400)


    now = time.time()
    last = float(request.session.get('last_comment_ts', 0) or 0)
    if now - last < COMMENT_COOLDOWN_SECONDS:
        wait = int(COMMENT_COOLDOWN_SECONDS - (now - last)) + 1
        return JsonResponse({'success': False,
                             'error': f'کمی آروم‌تر! {wait} ثانیه بعد دوباره نظر بده.'}, status=429)

    comment = form.save(commit=False)
    comment.content = content
    comment.user = request.user
    comment.article = article
    comment.parent = parent
    comment.is_approved = True
    comment.save()

    request.session['last_comment_ts'] = now
    request.session.modified = True

    html = render_to_string('single_comment.html', {
        'comment': comment,
        'user': request.user,
        'liked_comments': _session_list(request.session, 'liked_comments'),
    })

    return JsonResponse({
        'success': True,
        'html': html,
        'comment_id': comment.id,
        'parent_id': parent.id if parent else None,
        'comments_count': article.comments.filter(is_approved=True).count(),
    })


@require_POST
@login_required
def like_article(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    liked = _session_list(request.session, 'liked_articles')

    if article_id in liked:
        Article.objects.filter(pk=article_id, likes__gt=0).update(likes=F('likes') - 1)
        liked.remove(article_id)
        is_liked = False
    else:
        Article.objects.filter(pk=article_id).update(likes=F('likes') + 1)
        liked.append(article_id)
        is_liked = True
    request.session.modified = True

    article.refresh_from_db(fields=['likes'])
    return JsonResponse({'success': True, 'liked': is_liked, 'likes': article.likes})


def legacy_article_redirect(request, article_id):
    return redirect('blog:article_detail', article_id=article_id, permanent=True)


@require_POST
@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    liked = _session_list(request.session, 'liked_comments')

    if comment_id in liked:
        Comment.objects.filter(pk=comment_id, likes__gt=0).update(likes=F('likes') - 1)
        liked.remove(comment_id)
        is_liked = False
    else:
        Comment.objects.filter(pk=comment_id).update(likes=F('likes') + 1)
        liked.append(comment_id)
        is_liked = True
    request.session.modified = True

    comment.refresh_from_db(fields=['likes'])
    return JsonResponse({'success': True, 'liked': is_liked, 'likes': comment.likes})
