import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from access import group_required
from database.sql_provider import SQLProvider
from database.select import select_dict
from .model_route import (
    get_disciplines,
    get_projects_by_discipline,
    get_busy_teachers_by_date,
    get_schedule,
    create_commissions,
    model_route_delete,
)

blueprint_commission = Blueprint(
    'blueprint_commission',
    __name__,
    template_folder='templates'
)

# Провайдер SQL для commission/sql
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))


# ==========================
# Главная точка входа в модуль комиссий
# ==========================
@blueprint_commission.route('/', methods=['GET'])
@group_required
def commission_index():
    """
    Простой редирект на создание комиссии.
    """
    return redirect(url_for('blueprint_commission.create'))


# ==========================
# ШАГ 1: выбор преподавателей, дисциплины и даты
# ==========================
@blueprint_commission.route('/create', methods=['GET', 'POST'])
@group_required
def create():
    """
    Шаг 1: выбор преподавателей + дисциплины + даты.
    Никакого JS и AJAX — всё через GET/POST.
    """
    # На GET показываем форму
    if request.method == 'GET':
        return _render_step1()

    # POST — обрабатываем выбор
    teacher_ids = request.form.getlist('teacher_id')
    discipline_id = request.form.get('discipline_id')
    defense_date = request.form.get('defense_date')

    # Валидация: обязательно должны быть выбраны
    # - хотя бы один преподаватель
    # - дисциплина
    # - дата
    if not teacher_ids:
        return _render_step1(error='Выберите хотя бы одного преподавателя.')
    if not discipline_id or not defense_date:
        return _render_step1(error='Выберите дисциплину и дату комиссии.')

    # Сохраняем промежуточные данные в сессии
    try:
        session['order_teachers'] = [int(t) for t in teacher_ids]
    except ValueError:
        return _render_step1(error='Некорректный идентификатор преподавателя.')

    try:
        session['order_disc_id'] = int(discipline_id)
    except ValueError:
        return _render_step1(error='Некорректный идентификатор дисциплины.')

    session['order_date'] = defense_date

    # Переход на шаг выбора проектов
    return redirect(url_for('blueprint_commission.select_projects'))


def _render_step1(error: str | None = None):
    """Вспомогательная функция для рендера шага 1."""
    disciplines = get_disciplines(provider)
    teachers = select_dict(provider.get('teachers.sql'), {})
    return render_template(
        'order_select_step1.html',
        disciplines=disciplines,
        teachers=teachers,
        error=error
    )


# ==========================
# ШАГ 2: выбор проектов и создание комиссий
# ==========================
@blueprint_commission.route('/select-projects', methods=['GET', 'POST'])
@group_required
def select_projects():
    """
    Шаг 2:
      - GET: показываем доступные проекты по дисциплине, предупреждаем о занятых преподавателях.
      - POST: принимаем выбранные проекты, создаём комиссии, показываем результат.
    """
    teacher_ids = session.get('order_teachers')
    discipline_id = session.get('order_disc_id')
    defense_date = session.get('order_date')

    # Если пользователь зашёл сюда напрямую без шага 1 — отправим его обратно.
    if not teacher_ids or not discipline_id or not defense_date:
        return redirect(url_for('blueprint_commission.create'))

    # GET — показать форму выбора проектов
    if request.method == 'GET':
        # Список проектов по дисциплине
        projects = get_projects_by_discipline(provider, discipline_id)

        # Список занятых преподавателей на эту дату
        busy_teachers = get_busy_teachers_by_date(provider, defense_date)

        # Ограничим преподавателей только теми, кто свободен
        effective_teachers = [tid for tid in teacher_ids if tid not in busy_teachers]

        # ЖЁСТКАЯ защита: без свободных преподавателей комиссию создавать нельзя
        if not effective_teachers:
            clear_order_session()
            return _render_step1(
                error='На выбранную дату все выбранные преподаватели заняты. '
                      'Выберите другую дату или другой состав комиссии.'
            )

        # Сохраним свободных преподавателей отдельно
        session['order_teachers_effective'] = effective_teachers

        # Найдём название дисциплины для вывода
        disciplines = get_disciplines(provider)
        discipline_name = next(
            (d['name'] for d in disciplines if d['discipline_id'] == discipline_id),
            ''
        )

        return render_template(
            'order_select_step2.html',
            projects=projects,
            defense_date=defense_date,
            discipline_name=discipline_name,
            busy_teachers=busy_teachers
        )

    # POST — создание комиссий
    action = request.form.get('action')
    if action != 'create':
        return redirect(url_for('blueprint_commission.create'))

    project_ids = request.form.getlist('project_id')
    if not project_ids:
        # Ничего не выбрали — перерисуем тот же шаг с сообщением
        projects = get_projects_by_discipline(provider, discipline_id)
        busy_teachers = get_busy_teachers_by_date(provider, defense_date)
        disciplines = get_disciplines(provider)
        discipline_name = next(
            (d['name'] for d in disciplines if d['discipline_id'] == discipline_id),
            ''
        )
        return render_template(
            'order_select_step2.html',
            projects=projects,
            defense_date=defense_date,
            discipline_name=discipline_name,
            busy_teachers=busy_teachers,
            error='Выберите хотя бы один проект.'
        )

    # Сопоставим выбранные проекты с их полными данными
    all_projects = get_projects_by_discipline(provider, discipline_id)
    proj_map = {p['project_id']: p for p in all_projects}

    selected_projects = []
    for pid in project_ids:
        try:
            pid_int = int(pid)
        except ValueError:
            continue
        proj = proj_map.get(pid_int)
        if not proj:
            continue
        # Защита: не даём создать комиссию для проекта, у которого уже есть комиссия
        if proj.get('has_commission'):
            continue
        selected_projects.append(proj)

    if not selected_projects:
        projects = get_projects_by_discipline(provider, discipline_id)
        busy_teachers = get_busy_teachers_by_date(provider, defense_date)
        disciplines = get_disciplines(provider)
        discipline_name = next(
            (d['name'] for d in disciplines if d['discipline_id'] == discipline_id),
            ''
        )
        return render_template(
            'order_select_step2.html',
            projects=projects,
            defense_date=defense_date,
            discipline_name=discipline_name,
            busy_teachers=busy_teachers,
            error='Не удалось сопоставить выбранные проекты. Повторите выбор.'
        )

    # Используем список "эффективных" преподавателей (свободных на эту дату)
    effective_teachers = session.get('order_teachers_effective', teacher_ids)

    # Дополнительная защита: если по какой-то причине effective_teachers пуст —
    # не даём создать комиссию
    if not effective_teachers:
        clear_order_session()
        return _render_step1(
            error='Невозможно создать комиссию: не выбран ни один преподаватель. '
                  'Выберите состав комиссии заново.'
        )

    # Создаём комиссии (логика уже есть в model_route.create_commissions)
    created, skipped = create_commissions(
        provider,
        effective_teachers,
        selected_projects,
        defense_date
    )

    # Очищаем временные данные
    clear_order_session()

    return render_template(
        'commission_result.html',
        created=created,
        skipped=skipped
    )


def clear_order_session():
    """Вспомогательная функция: очистка временных данных по формированию комиссии."""
    for key in ['order_teachers', 'order_disc_id', 'order_date', 'order_teachers_effective']:
        session.pop(key, None)


# ==========================
# РАСПИСАНИЕ
# ==========================
@blueprint_commission.route('/schedule', methods=['GET'])
@group_required
def schedule():
    """
    Просмотр расписания комиссий без JS.
    """
    schedule = get_schedule(provider)
    return render_template('schedule_simple.html', schedule=schedule)


@blueprint_commission.route('/delete', methods=['POST'])
@group_required
def delete_cs():
    """
    Удаление комиссии (и её членов) обычной HTML-формой POST.
    Ожидаем project_id (как в текущих SQL-файлах).
    """
    project_id = request.form.get('project_id')

    if not project_id:
        return render_template('commission_err.html', error='удалении комиссии')

    try:
        project_id_int = int(project_id)
    except ValueError:
        return render_template('commission_err.html', error='удалении комиссии')

    # model_route_delete ожидает словарь с project_id
    model_route_delete(provider, {'project_id': project_id_int})

    return redirect(url_for('blueprint_commission.schedule'))