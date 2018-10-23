from openpyxl import load_workbook
import pymysql
import time
import datetime
import requests

TIME_ON_STRING = "07:50"
TIME_OFF_STRING = "16:35"


def insert_database(list_line):
    """
    将excel中的数据批量插入数据库中
    :param list_line: 列表数据，存放行的列表信息
    :return:
    """
    connection = get_connect()
    for line in list_line:
        with connection.cursor() as cursor:
            sql = " insert into bt_att_t (att_date, att_starttime, att_endtime, sign_holiday) values ( %s, %s, %s, %s ) "
            cursor.execute(sql, (line[0], line[1], line[2], line[3]))
    connection.commit()
    connection.close()


def close_connect(connect):
    connect.commit()
    connect.close()


def get_holiday_sign(list_date):
    """
    通过第三方API判断日期是否位节假日
    :param list_date:
    :return:
    """
    param = ",".join(list_date).replace("-", "")
    url = "http://www.easybots.cn/api/holiday.php?d="+param
    r = requests.get(url)
    return r.json()


def read_excel(path):

    wb = load_workbook(path)
    ws = wb.active
    rows = ws.rows

    index_date = -1
    index_start = -1
    index_end = -1
    list_date = []
    list_line = []

    row_number = 0
    for row in rows:
        line = [col.value for col in row]
        row_number += 1
        if row_number == 1:
            for i in range(0, len(line)):
                if "日期" == line[i]:
                    index_date = i
                elif "签到时间" == line[i]:
                    index_start = i
                elif "签退时间" == line[i]:
                    index_end = i
        elif index_date != -1 and index_start != -1 and index_end != -1:
            str_date = line[index_date]
            date = time.strptime(str_date, '%Y/%m/%d')
            str_date = time.strftime('%Y-%m-%d', date)
            start_time = line[index_start].strip()
            end_time = line[index_end].strip()
            start_time = None if start_time == "" else start_time
            end_time = None if end_time == "" else end_time
            line_need = [str_date, start_time, end_time]
            list_line.append(line_need)
            list_date.append(str_date)

    json_holiday = get_holiday_sign(list_date)
    for line_need in list_line:
        date = line_need[0].replace("-", "")
        sign_holiday = json_holiday[date]
        line_need.append(sign_holiday)

    insert_database(list_line)


def get_connect():
    return pymysql.connect("localhost", "root", "root", "attendance")


def get_overtime_in_workday(month):
    connect = get_connect()
    with connect.cursor() as cursor:
        month = "%" + month + "%"
        sql = """
        select att_date, att_starttime, att_endtime, sign_holiday from bt_att_t where att_date like %s order by att_date desc 
        """
        cursor.executemany(sql, [month])
        result = cursor.fetchall()
        close_connect(connect)
        list_dict = []
        for line in result:
            date_str = line[0]
            start_str = line[1]
            end_str = line[2]
            holiday_int = line[3]
            # 节假日加班
            if holiday_int != 0 and not start_str and not end_str:
                date_datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                time_date = date_datetime.date()

                start_datetime = datetime.datetime.strptime(start_str, '%H:%M')
                end_datetime = datetime.datetime.strptime(end_str, '%H:%M')
                start_datetime = datetime.datetime.combine(time_date, start_datetime.time())
                end_datetime = datetime.datetime.combine(time_date, end_datetime.time())

                hours = round((end_datetime-start_datetime).seconds/3600, 1)
                title = "节假日加班%s小时" % str(hours)
                json = {"title": title, "start": line[0], "end": line[0]}
                list_dict.append(json)
            # 工作日加班
            elif holiday_int == 0 and not start_str and not end_str:
                date_datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                time_date = date_datetime.date()
                start_datetime = datetime.datetime.strptime(start_str, '%H:%M')
                end_datetime = datetime.datetime.strptime(end_str, '%H:%M')
                on_time = datetime.datetime.strptime(TIME_ON_STRING, '%H:%M')
                off_time = datetime.datetime.strptime(TIME_OFF_STRING, '%H:%M')

                start_datetime = datetime.datetime.combine(time_date, start_datetime.time())
                end_datetime = datetime.datetime.combine(time_date, end_datetime.time())
                on_time = datetime.datetime.combine(time_date, on_time.time())
                off_time = datetime.datetime.combine(time_date, off_time.time())
                if (on_time - start_datetime).seconds > 1800 and (end_datetime - off_time).seconds > 1800 :
                    result


def get_overtime_in_holiday(month):
    """
    节假日加班
    :param month:
    :return:
    """
    connect = get_connect()
    with connect.cursor() as cursor:
        month = "%" + month + "%"
        sql = """select att_date, att_starttime, att_endtime 
                  from bt_att_t 
                  where att_starttime is not null and 
                  att_endtime is not null and 
                  sign_holiday<>0 and 
                  att_date like %s 
                  order by att_date desc"""

        cursor.executemany(sql, [month])
        result = cursor.fetchall()
    close_connect(connect)
    list_dict = []
    for line in result:
        date_datetime = datetime.datetime.strptime(line[0], "%Y-%m-%d")
        time_date = date_datetime.date()

        start_datetime = datetime.datetime.strptime(line[1], '%H:%M')
        end_datetime = datetime.datetime.strptime(line[2], '%H:%M')
        start_datetime = datetime.datetime.combine(time_date, start_datetime.time())
        end_datetime = datetime.datetime.combine(time_date, end_datetime.time())

        hours = round((end_datetime-start_datetime).seconds/3600, 1)
        title = "节假日加班%s小时" % str(hours)
        json = {"title": title, "start": line[0], "end": line[0]}
        list_dict.append(json)
        print()

    return list_dict


def get_calendar():
    connect = get_connect()
    with connect.cursor() as cursor:
        cursor.execute(" select * from bt_att_t "
                       "where att_date is not null and "
                       "att_starttime is not null and "
                       "att_endtime is not null and sign_holiday<>0 ")

        result = cursor.fetchall()
        print(result)

# read_excel('C:\\Users\\yhr\\Desktop\\考勤20181019.xlsx')


