import pymysql
from django.shortcuts import render
from django.http import HttpResponse
from django_ajax.decorators import ajax
from .demo.excel import get_calendar_dates, add_kq_content
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
    result = get_calendar_dates(month)
    # with connect.cursor() as cursor:
    #     sql = " select att_date, att_starttime, att_endtime from  bt_att_t where att_date like concat('%%', %s,'%%') "
    #     cursor.executemany(sql, (month))
    #     result = cursor.fetchall()
    #     for head in result:
    #         line = list(head)
    #         print(line)
    return {'data': result}


@ajax
def ajax_add_kq_content(request):
    content = request.POST.get("content")
    day = request.POST.get("date")
    add_kq_content(content, day)
    return {'data': day}
