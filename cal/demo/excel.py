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


def get_calendar_dates(month):
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
            date_dict = get_base_dict(date_str, start_str, end_str, holiday_int)

            date_datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            time_date = date_datetime.date()
            on_time = datetime.datetime.strptime(TIME_ON_STRING, '%H:%M')
            on_time = datetime.datetime.combine(time_date, on_time.time())
            off_time = datetime.datetime.strptime(TIME_OFF_STRING, '%H:%M')
            off_time = datetime.datetime.combine(time_date, off_time.time())

            if start_str is not None:
                start_datetime = datetime.datetime.strptime(start_str, '%H:%M')
                start_datetime = datetime.datetime.combine(time_date, start_datetime.time())
                # 上午加班
                is_overtime_start = (on_time - start_datetime).seconds > 1800
                # 迟到
                is_late = (on_time - start_datetime).seconds < 0
                # 上午加班耗时
                overtime_hours_start = abs(round((on_time - start_datetime).seconds/3600, 1))
            if end_str is not None:
                end_datetime = datetime.datetime.strptime(end_str, '%H:%M')
                end_datetime = datetime.datetime.combine(time_date, end_datetime.time())
                # 下午加班
                is_overtime_end = (end_datetime - on_time).seconds > 1800
                # 早退
                is_leave_early = (end_datetime - on_time).seconds < 0
                # 下午加班耗时
                overtime_hours_end = abs(round((end_datetime - on_time).seconds/3600, 1))

            # 节假日加班
            if holiday_int != 0 and start_str is not None and end_str is not None:
                hours = round((end_datetime-start_datetime).seconds/3600, 1)
                title = "节假日加班%s小时" % str(hours)
                json = get_overtime_dict(date_dict, title)
                list_dict.append(json)
            # 工作日 and 上午打卡 and 下午打卡
            elif holiday_int == 0 and start_str is not None and end_str is not None:
                # 加班
                if is_overtime_start and is_overtime_end:
                    hours = overtime_hours_start + overtime_hours_end
                    title = "工作日加班%s小时" % str(hours)
                    json = get_overtime_dict(date_dict, title)
                    list_dict.append(json)
                # 迟到早退
                elif is_late and is_leave_early:
                    title = "上班迟到%s，下班早退%s" % (str(overtime_hours_start), str(overtime_hours_end))
                    json = get_late_early_dict(date_dict, title)
                    list_dict.append(json)
                # 迟到
                elif is_late:
                    title = "上班迟到%s" % (str(overtime_hours_start))
                    json = get_late_early_dict(date_dict, title)
                    list_dict.append(json)
                # 早退
                elif is_leave_early:
                    title = "下班早退%s" % (str(overtime_hours_end))
                    json = get_late_early_dict(date_dict, title)
                    list_dict.append(json)
            # 工作日 or 矿工 or 缺少上午或下午打卡记录
            elif holiday_int == 0:
                # 旷工一天
                if start_str is None and end_str is None:
                    title = "矿工"
                    json = get_absent_dict(date_dict, title)
                    list_dict.append(json)
                # 上午未打卡
                elif start_str is None and end_str is not None:
                    # 早退
                    if (off_time - end_datetime).seconds > 0:
                        hours = overtime_hours_end
                        title = "早上未打卡，下班打卡时间%s，早退%s小时" % (end_str, str(hours))
                    # 正常
                    else:
                        title = "早上未打卡"
                    json = get_incomplete_dict(date_dict, title)
                    list_dict.append(json)
                # 下午未打卡，上午迟到或正常
                elif end_str is None and start_str is not None:
                    # 迟到
                    if (start_datetime - on_time).seconds > 0:
                        hours = overtime_hours_start
                        title = "下午未打卡，上班打卡时间%s，迟到%s小时" % (start_str, str(hours))
                    # 正常
                    else:
                        title = "下午未打卡"
                    json = get_incomplete_dict(date_dict, title)
                    list_dict.append(json)

    return list_dict


def __get_dict__(date_dict, title, color):
    """
    数据样式
    :param title:
    :param date_string:
    :param time_start_work:
    :param time_end_work:
    :param color:
    :return:
    """
    date_dict["title"] = title

    if color is not None:
        date_dict["color"] = color

    return date_dict


def get_absent_dict(date_dict, title):
    """
    旷工时的数据样式
    :param title:
    :param date_string:
    :param time_start_work:
    :param time_end_work:
    :return:
    """
    return __get_dict__(date_dict=date_dict, title=title, color="red")


def get_overtime_dict(date_dict, title):
    """
    标准加班的数据样式
    :param title:
    :param date_string:
    :param time_start_work:
    :param time_end_work:
    :return:
    """
    return __get_dict__(date_dict, title, None)


def get_late_early_dict(date_dict, title):
    """
    迟到早退的数据样式
    :param title:
    :param date_string:
    :param time_start_work:
    :param time_end_work:
    :return:
    """
    return __get_dict__(date_dict, title, "yellow")


def get_incomplete_dict(date_dict, title):
    """
    缺少上午或下午打卡记录的数据样式
    :param title:
    :param date_string:
    :param time_start_work:
    :param time_end_work:
    :return:
    """
    return __get_dict__(date_dict, title, "gray")


def get_base_dict(date_string, time_start_work, time_end_work, holiday):

    tooltip = ""
    if time_start_work is not None:
        tooltip = "上班打卡时间："+time_start_work+" \n下班打卡时间：未打卡"
    if time_end_work is not None:
        tooltip = "上班打卡时间：未打卡 \n下班打卡时间："+time_end_work
    if time_start_work is None and time_end_work is None:
        tooltip = "上班打卡时间：未打卡 \n下班打卡时间：未打卡"

    base = {"start": date_string, "end": date_string, "tooltip": tooltip}

    # if holiday != 0:
    #     base["color"] = "#ff9f89"
    #     base["rendering"] = "background"

    return base


# read_excel('C:\\Users\\yhr\\Desktop\\考勤20181019.xlsx')


