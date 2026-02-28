from dataclasses import dataclass
from database.select import select_dict

@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route(provider, user_input: dict, sql_file: str):
    err_message = ""
    _sql = provider.get(sql_file)
    print("sql=",_sql)
    result = select_dict(_sql, user_input)
    print("result=", result)
    if result:
        return ResultInfo(result=result, status=True, err_message=err_message)
    else:
        print("DATA NOT FOUND")
        return ResultInfo(result=result, status=False, err_message="DATA NOT FOUND")