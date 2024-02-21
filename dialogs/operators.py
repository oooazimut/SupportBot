import operator

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from states import OperatorSG
from db import task_service, empl_service


async def operator_getter(dialog_manager: DialogManager, **kwargs):
    userid = dialog_manager.middleware_data['user_id'].id
    un = empl_service.get_employee('',userid = userid)
    return {'un': un}


dialog = Dialog(
    Window (
        Const("Главное меню:"),
        Row(
            Button(Const('Заявки'), id = 'tasks', on_click=),
            Button(Const('Работники'), id = 'slaves', on_click=)
        ),
        state = OperatorSG.main
    ),

    Window(
        Const('Заявки:'),
           Row(
               Button(Const('Новые заявки'), id='assign', on_click=),
               Button(Const('Заявки в работе'), id='done', on_click=),
               Button(Const('Архив'), id='archive', on_click=)
           ),
        SwitchTo(Const('Назад'), id = 'to_main',state = OperatorSG.main),
        state = OperatorSG.tas
    ),

    Window(
        Const('Новые заявки:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='new_tasks',
                item_id_getter=operator.itemgetter('id'),
                items=''
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state = OperatorSG.new_task,
        getter = task_service.get_new_tasks_getter
    ),

    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='in_progress_tasks',
                item_id_getter=operator.itemgetter('id'),
                items=''
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.progress_task,
        getter=task_service.get_in_progress_tasks_getter
    ),

    Window(
        Const('Заявки в архиве'),
      Column(
          Select(
              Format('{item[title]} {item[priority]}'),
              id='done_tasks',
              item_id_getter=operator.itemgetter('id'),
              items=''
          )
      ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.done_task,
        getter=task_service.get_done_tasks_getter
    ),

    Window(
        Const('Работники:'),
        Row(
            Button(Const('Операторы'), id='assigned', on_click=),
            Button(Const('Исполнители'), id='worker_archive', on_click=)
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state = OperatorSG.worker
    ),

    Window(
        Const('Список операторов:'),
        Column(
            Select(
                Format('{item[name]} {item[surname]}'),
                id='operators',
                item_id_getter=operator.itemgetter('id'),
                items=''
            )
        ),

        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state = OperatorSG.opr,
        getter = operator_getter
    ),

    Window(
      Const('Список работников:'),
        Column(
          Select(
              Format('{item[name]} {item[surname]}'),
              id = 'workers',
              item_id_getter = operator.itemgetter('id'),
              items = ''
          )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state = OperatorSG.opr,
        getter =
    ),
    Window(
      Const('')
    ),


)