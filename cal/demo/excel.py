from openpyxl import load_workbook


def read_excel(path):
    wb = load_workbook(path)
    # names = wb.sheetnames
    ws = wb.active
    rows = ws.rows
    columns = ws.columns
    # header = rows[0]

    # print(wb.sheetnames)
    xls_head_kqnumber = "考勤号码"
    xls_head_name = "姓名"
    xls_head_date = "日期"
    xls_head_onwork = "上班时间"
    xls_head_offwork = "下班时间"
    xls_head_start = "签到时间"
    xls_head_end = "签退时间"
    xls_head_dept = "部门"

    xls_index_kqnumber = -1
    xls_index_name = -1
    xls_index_date = -1
    xls_index_onwork = -1
    xls_index_offwork = -1
    xls_index_start = -1
    xls_index_end = -1
    xls_index_dept = -1

    col_count = ws.max_column
    while col_count > 0:
        cell_value = str(ws.cell(1, col_count, None).value)
        if xls_head_kqnumber == cell_value:
            xls_index_kqnumber = col_count
        elif xls_head_name == cell_value:
            xls_index_name = col_count
        elif xls_head_date == cell_value:
            xls_index_date = col_count
        elif xls_head_onwork == cell_value:
            xls_index_onwork = col_count
        elif xls_head_offwork == cell_value:
            xls_index_offwork = col_count
        elif xls_head_start == cell_value:
            xls_index_start = col_count
        elif xls_head_end == cell_value:
            xls_index_end = col_count
        elif xls_head_dept == cell_value:
            xls_index_dept = col_count
        col_count -= 1




    for row in rows:
        line = [col.value for col in row]
        print(line)


read_excel('C:\\Users\\yhr\\Desktop\\考勤.xlsx')
