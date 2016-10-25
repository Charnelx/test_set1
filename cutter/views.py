from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.template import loader
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from .forms import UrlForm
import base64


from django.core.urlresolvers import reverse

def indexToBase(n,base):
   convertString = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
   if n < base:
      return convertString[n]
   else:
      return indexToBase(n // base, base) + convertString[n % base]

# redirect_or_404 view
def tiny_redirect(request, turl):
    url = cache.get(turl)
    if not url:
        return HttpResponseNotFound(b'Not found!')
    else:
        return HttpResponseRedirect(url)


def cutter(request):
    if request.method == 'POST':
        form = UrlForm(request.POST)

        if form.is_valid():
            c_form = form.cleaned_data

            # get url from form POST'ed data
            url = c_form['turl']

            domain = request.META['HTTP_HOST']

            url_index = cache.get('url_index', default=-1)
            if url_index == -1:
                # starts from 999 to make link's little bit serious
                url_index = 999
                cache.set('url_index', url_index, timeout=None)

            # inc unique index
            url_index = cache.incr('url_index', delta=1)
            # make short integer representation
            base_index = indexToBase(url_index, 62)

            # add base index as key if does not exists yet
            if not cache.get(base_index):
                # save {base_index: full_url}
                cache.add(base_index, url, timeout=None)

            link = base64.urlsafe_b64encode('{0}/{1}'.format(domain, base_index).encode('utf-8'))
            return HttpResponseRedirect(reverse('index', kwargs={'id': link}))

# save in cache for 5 minuts
@cache_page(60 * 5)
def index(request, id=None):

    # is our counters in Redis?
    total_visits = cache.get('total_visits', default=-1)

    # nope; it's first run. Lets init them.
    if total_visits == -1:
        total_visits = 0
        unique_visits = 1
        cache.set_many({'total_visits': total_visits, 'unique_visits': unique_visits}, timeout=None)

    template = loader.get_template('cutter/index.html')

    if not id:
        # default value for URL input form
        form_default = ''

        # we never see user before? Say hello and give him a cookie
        if 'visited' not in request.COOKIES:
            unique_visits = cache.incr('unique_visits', delta=1)

            context = {
            'counters': True,
            'unique': True,
            'total_visit': total_visits,
            'unique_visit': unique_visits,
            'form_default': form_default,
            }
            response = HttpResponse(template.render(context, request))
            # cookie lifetime set to one day
            response.set_cookie("visited", True, max_age=1 * 24 * 60 * 60)
            return response
        else:
            total_visits = cache.incr('total_visits', delta=1)
            unique_visits = cache.get('unique_visits')

            context = {
                'counters': True,
                'unique': False,
                'total_visit': total_visits,
                'unique_visit': unique_visits,
                'form_default': form_default,
            }
            return HttpResponse(template.render(context, request))
    else:
        unique_visits = cache.get('unique_visits')

        context = {
            'counters': True,
            'unique': False,
            'total_visit': total_visits,
            'unique_visit': unique_visits,
            'form_default': base64.urlsafe_b64decode(id).decode('utf-8'),
        }
        return HttpResponse(template.render(context, request))