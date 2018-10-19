from django.shortcuts import render
from django.http import HttpResponse
from django_ajax.decorators import ajax
import pymysql
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
    connect = pymysql.connect("localhost", "root", "root", "attendance")
    with connect.cursor() as cursor:
        sql = " select att_date, att_starttime, att_endtime from  bt_att_t where att_date like concat('%%', %s,'%%') "
        cursor.executemany(sql, (month))
        result = cursor.fetchall()
        for head in result:
            line = list(head)
            print(line)
    return {'data': result}
