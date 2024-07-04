import operator

from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo, Cancel, Start, Back, Next, ScrollingGroup
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja
from magic_filter import F

import config
from db import task_service
from getters.operators import review_getter, addition_getter, act_getter, with_acts_getter, objects_getter
from handlers import operators
from handlers.operators import on_addit, on_back_to_preview, on_return, delay_handler, on_act, to_all_tasks
from states import OperatorSG, WorkersSG, OpTaskSG, TaskCreating, DelayTaskSG, ObjectsSG

JINJA_TEMPLATE = Jinja('{% set dttm_list = item.created.split() %}'
                       '{% set dt_list = dttm_list[0].split("-") %}'
                       '{% set dt = dt_list[2]+"."+dt_list[1] %}'
                       '{% set d = "\U0000231B" if item.status == "отложено" else "" %}'
                       '{% set st = "\U00002705" if item.status == "выполнено" else "\U0001F7E9" if item.status == '
                       '"в работе" else "" %}'
                       '{% set sl = item.username if item.username else "\U00002753" %}'
                       '{% set pr = item.priority if item.priority else "" %}'
                       '{% set ob = item.name if item.name else "" %}'
                       '{% set tt = item.title if item.title else "" %}'
                       '{% set ag = "\U00002757\U0001F4DE\U00002757" if item.agreement else "" %}'
                       '{{ag}}{{d}}{{st}} {{dt}} {{pr}} {{sl}} {{ob}} {{tt}}')

main_dialog = Dialog(
    Window(
        Const("Главное меню:"),
        Row(
            Start(Const('Заявки'), id='tasks', state=OpTaskSG.tas),
            Start(Const('Работники'), id='slaves', state=WorkersSG.main),
            Start(Const('Объекты'), id='ojects', state=ObjectsSG.main)
        ),
        state=OperatorSG.main
    ),
)


def acts_are_existing(data, widget, manager: DialogManager):
    userid = manager.event.from_user.id
    return bool(task_service.get_tasks_by_status('проверка')) and userid == config.DEV_ID


task_dialog = Dialog(
    Window(
        Const('Заявки:'),
        Row(
            Button(Const('Открытые'), id='tasks', on_click=operators.on_tasks),
            Button(Const('Архив'), id='archive', on_click=operators.go_archive),
        ),
        SwitchTo(Const('Проверить акты'), id='to_acts', state=OpTaskSG.with_acts, when=acts_are_existing),
        Start(Const('Создать заявку'), id='new_op_task', data={}, state=TaskCreating.sub_entity),
        Cancel(Const('Назад')),
        state=OpTaskSG.tas
    ),
    Window(
        Const('Открытые заявки:'),
        Column(
            Select(
                JINJA_TEMPLATE,
                id='new_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=operators.on_task
            )
        ),
        Button(Const('Обновить'), id='reload_opened'),
        SwitchTo(Const('Назад'), id='to_main', state=OpTaskSG.tas),
        state=OpTaskSG.opened_tasks,
        getter=operators.tasks_getter,
        parse_mode='html'
    ),
    Window(
        Const('Заявки в архиве'),
        Column(
            Select(
                JINJA_TEMPLATE,
                id='done_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=operators.on_task
            )
        ),
        Button(Const('Обновить'), id='reload_archived'),
        SwitchTo(Const('Назад'), id='to_main', state=OpTaskSG.tas),
        state=OpTaskSG.archive_task,
        getter=operators.tasks_getter,
        parse_mode='html'
    ),
    Window(
        Jinja('''
       {{created}}
       Тема: {{title if title}}
       Объект: {{name if name}}
       Описание: {{description if description}}
       Исполнитель: {{username if username}}
       Приоритет: {{priority if priority}}
       Статус: {{status}}
       '''),
        Format('Нужен акт', when=F['act']),
        Format('<b><i><u>Согласование: {agreement}</u></i></b>', when=F['agreement']),
        Format('\n <b>Информация по закрытию:</b> \n {summary}', when=F['summary']),
        DynamicMedia('resultmedia', when=F['resultmedia']),
        Button(Const('Доп инфо'), id='addit_info', on_click=on_addit, when=F['media_id']),
        Button(Const('Акт'), id='act', on_click=on_act, when=F['actid']),
        Button(Const('Редактировать'), id='edit_task', on_click=operators.edit_task, when=(F['status'] != 'закрыто')),
        Button(Const('Отложить'), id='delay_task', on_click=operators.on_delay, when=(F['status'] != 'отложено')),
        Button(Const('Переместить в архив'), id='close_task', on_click=operators.to_confirmation,
               when=(F['status'] != 'закрыто')),
        Button(Const('Вернуть в работу'), id='return_to_work', on_click=on_return, when=(F['status'] == 'выполнено')),
        Button(Const('Назад'), id='to_all_tasks', on_click=to_all_tasks),
        state=OpTaskSG.preview,
        getter=review_getter,
    ),
    Window(
        Const('Вы уверены, что хотите закрыть заявку?'),
        Back(Const('нет')),
        Next(Const('да')),
        state=OpTaskSG.close_confirmation
    ),
    Window(
        Const('Здесь можно добавить информацию по закрытию заявки:'),
        TextInput(id='summary', on_success=operators.on_close),
        state=OpTaskSG.summary
    ),
    Window(
        Const('Проверить акты:'),
        Column(
            Select(
                JINJA_TEMPLATE,
                id='tasks_with_acts',
                item_id_getter=lambda x: x['taskid'],
                items='tasks',
                on_click=operators.on_task
            ),
        ),
        state=OpTaskSG.with_acts,
        getter=with_acts_getter
    ),
    Window(
        DynamicMedia('media'),
        Button(Const('Назад'), id='to_preview', on_click=on_back_to_preview),
        state=OpTaskSG.additional,
        getter=addition_getter
    ),
    Window(
        DynamicMedia('media'),
        Button(Const('Назад'), id='to_preview', on_click=on_back_to_preview),
        state=OpTaskSG.act,
        getter=act_getter
    )
)

DelayDialog = Dialog(
    Window(
        Const('Введите количество дней, на которое вы хотите отложить заявку'),
        MessageInput(delay_handler, content_types=[ContentType.TEXT]),
        Cancel(Const('Назад')),
        state=DelayTaskSG.enter_delay
    ),
    Window(
        Format('Ваша заявка отложена до {dialog_data[trigger]}'),
        Button(Const('Хорошо'), id='on_done', on_click=operators.on_done),
        state=DelayTaskSG.done
    )
)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get('finished'):
        await dialog_manager.switch_to(TaskCreating.preview)
    else:
        await dialog_manager.next()


CANCEL_EDIT = SwitchTo(
    Const("Отменить редактирование"),
    when=F["dialog_data"]['finished'],
    id="cnl_edt",
    state=TaskCreating.preview
)

worker_dialog = Dialog(
    Window(
        Const('Работники:'),
        Row(
            Button(Const('Операторы'), id='assigned', on_click=operators.go_operator),
            Button(Const('Исполнители'), id='worker_archive', on_click=operators.go_worker),
            Button(Const('Добавить работника'), id='add_worker', on_click=operators.go_addslaves),
        ),
        Cancel(Const('Назад')),
        state=WorkersSG.main
    ),

    Window(
        Const('Список операторов:'),
        Column(
            Select(
                Format('{item[username]}'),
                id='operators',
                item_id_getter=operator.itemgetter('userid'),
                items='un'
            )
        ),

        SwitchTo(Const('Назад'), id='to_main', state=WorkersSG.main),
        state=WorkersSG.opr,
        getter=operators.operator_getter
    ),

    Window(
        Const('Список работников:'),
        Column(
            Select(
                Format('{item[username]}'),
                id='workers',
                item_id_getter=operator.itemgetter('userid'),
                items='un'
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkersSG.main),
        state=WorkersSG.slv,
        getter=operators.worker_getter
    ),

    Window(
        Const('Введите имя сотрудника'),
        TextInput(id='user_name', on_success=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=WorkersSG.add_slv
    ),
    Window(
        Const('Введите id сотрудника'),
        TextInput(id='user_id', on_success=next_or_end),
        Back(Const('Назад')),
        Cancel(Const('Отменить создание')),
        state=WorkersSG.add_id
    ),
    Window(
        Const('Выберите статус для сотрудника'),
        Column(
            Button(Const('Исполнитель'), id='slaves_status', on_click=operators.insert_slaves),
            Button(Const('Оператор'), id='operator_status', on_click=operators.insert_operator)
        ),
        Back(Const('Назад')),
        CANCEL_EDIT,
        state=WorkersSG.status

    )
)


objects = Dialog(
    Window(
        Const('Функционал объектов'),
        SwitchTo(Const('Все объекты'), id='to_all', state=ObjectsSG.allinone),
        SwitchTo(Const('Поиск'), id='to_search', state=ObjectsSG.search),
        SwitchTo(Const('Добавить объект'), id='to_adding', state=ObjectsSG.add),
        Cancel(Const('Назад')),
        state=ObjectsSG.main
    ),
    Window(
        Const('Все объекты'),
        ScrollingGroup(
            Select(
                Format('item[name]'),
                id='sel_objects',
                item_id_getter=lambda x: x['ent_id'],
                items='objects',
                on_click=on_object
            ),
            id='scroll_objects',
            width=2,
            height=10,
            hide_on_single_page=True
        ),
        state=ObjectsSG.allinone,
        getter=objects_getter
    ),
    Window(
        state=ObjectsSG.search
    ),
    Window(
        state=ObjectsSG.add
    ),
)
