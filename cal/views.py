from django.shortcuts import render
from django.http import HttpResponse
from django_ajax.decorators import ajax
# Create your views here.


def calendar(request, user_id):
    user_id = "Welcome，Your login name is %s" % user_id
    return HttpResponse(user_id)


def index(request):
    # html = render_to_string("index.html")
    # return HttpResponse(html)
    return render(request, "index.html")


@ajax
def ajax_demo(request):
    month = request.GET.get('month')
    return {'data': month}
