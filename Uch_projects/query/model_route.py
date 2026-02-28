from dataclasses import dataclass
from database.select import select_dict

@dataclass
class ResultInfo:
    result: list
    status: bool
    err_message: str


def model_route(provider, user_input: dict, sql_file: str):
    _sql = provider.get(sql_file)
    result = select_dict(_sql, user_input)

    if result:
        return ResultInfo(result=result, status=True, err_message="")
    else:
        return ResultInfo(result=[], status=False, err_message="DATA NOT FOUND")
