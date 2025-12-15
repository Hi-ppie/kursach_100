import os
import json
from flask import Blueprint, render_template, request
from access import group_required
from query.model_route import model_route
from database.sql_provider import SQLProvider

blueprint_query = Blueprint(
    'blueprint_query',
    __name__,
    template_folder='templates'
)

provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

with open("data/query.json", encoding="utf-8") as f:
    query_dict = json.load(f)

@blueprint_query.route('/', methods=["GET"])
@group_required
def query_menu():
    return render_template("query_menu.html")

@blueprint_query.route('/query', methods=["GET"])
@group_required
def query_index():
    query_id = request.args.get('id')
    return render_template(query_dict[query_id]['input'])

@blueprint_query.route('/result', methods=["POST"])
@group_required
def query_result():
    query_id = request.args.get('id')
    user_input = request.form.to_dict()

    result_info = model_route(
        provider,
        user_input,
        query_dict[query_id]['file_name']
    )

    if result_info.status:
        return render_template(
            query_dict[query_id]['output'],
            results=result_info.result,
            id=query_id
        )
    else:
        return render_template("err.html", id=query_id)
