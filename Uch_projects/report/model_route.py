from dataclasses import dataclass
from database.select import select_list, stored_proc


@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route_create(proc_name: str, rep_type: str, user_input: dict):
    """
    Формирование отчёта через процедуру make_report
    """

    if rep_type == 'by_date':
        user_list = [
            rep_type,
            int(user_input['month']),
            int(user_input['year']),
            None
        ]

    elif rep_type == 'by_teacher':
        user_list = [
            rep_type,
            None,
            None,
            int(user_input['teacher_id'])
        ]
    else:
        return False

    message = stored_proc(proc_name, user_list)
    if not message:
        return False

    return message


def model_route_show(provider, rep_type: str, user_input: dict, sql_file: str):
    """
    Отображение отчёта
    """

    if rep_type == 'by_date':
        sql_params = [
            int(user_input['month']),
            int(user_input['year'])
        ]

    elif rep_type == 'by_teacher':
        sql_params = [
            int(user_input['teacher_id'])
        ]
    else:
        return ResultInfo(result=(), status=False, err_message="UNKNOWN REPORT TYPE"), ()

    _sql = provider.get(sql_file)
    result, schema = select_list(_sql, sql_params)

    if result:
        return ResultInfo(result=result, status=True, err_message=""), schema
    else:
        return ResultInfo(result=result, status=False, err_message="DATA NOT FOUND"), schema
