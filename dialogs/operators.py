import operator

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from states import OperatorSG, TaskSG, WorkersSG
from db import task_service, empl_service
import handlers.operator_handler




main_dialog = Dialog(
    Window (
        Const("Главное меню:"),
        Row(
            Button(Const('Заявки'), id='tasks', on_click=handlers.operator_handler.go_task),
            Button(Const('Работники'), id='slaves', on_click=handlers.operator_handler.go_slaves),
        ),
        state=OperatorSG.main
    ),
)
task_dialog = Dialog(
    Window(
        Const('Заявки:'),
           Row(
               Button(Const('Новые заявки'), id='assign', on_click=handlers.operator_handler.go_new_task),
               Button(Const('Заявки в работе'), id='done', on_click=handlers.operator_handler.go_work_task),
               Button(Const('Архив'), id='archive', on_click=handlers.operator_handler.go_archive)
           ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.tas
    ),

    Window(
        Const('Новые заявки:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='new_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks'
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=TaskSG.new_task,
        getter=task_service.get_new_tasks_getter
    ),

    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='in_progress_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks'
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=TaskSG.progress_task,
        getter=handlers.operator_handler.progress_task_getter,
    ),

    Window(
        Const('Заявки в архиве'),
      Column(
          Select(
              Format('{item[title]}'),
              id='done_tasks',
              item_id_getter=operator.itemgetter('id'),
              items='task'
          )
      ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=TaskSG.archive_task,
        getter=handlers.operator_handler.archive_getter
    ),
)

worker_dialog = Dialog(
    Window(
        Const('Работники:'),
        Row(
            Button(Const('Операторы'), id='assigned', on_click=handlers.operator_handler.go_operator),
            Button(Const('Исполнители'), id='worker_archive', on_click=handlers.operator_handler.go_worker)
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.worker
    ),

    Window(
        Const('Список операторов:'),
        Column(
            Select(
                Format('{item[name]} {item[surname]}'),
                id='operators',
                item_id_getter=operator.itemgetter('id'),
                items='un'
            )
        ),

        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=WorkersSG.opr,
        getter=handlers.operator_handler.operator_getter
    ),

    Window(
      Const('Список работников:'),
        Column(
          Select(
              Format('{item[name]} {item[surname]}'),
              id='workers',
              item_id_getter=operator.itemgetter('id'),
              items='un'
          )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=WorkersSG.slv,
        getter=handlers.operator_handler.worker_getter
    ),
)
def is_opened(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'назначено'


def not_in_archive(data, widget, manager: DialogManager):
    return manager.start_data['status'] != 'закрыто'


def is_performed(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'выполнено'


def is_in_progress(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'в работе'

edit_task_dialog = Dialog(
    Window(
        Format('{start_data[created]}'),
        Format('{start_data[name]}'),
        Format('{start_data[title]}'),
        Format('{start_data[description]}'),
        Format('Приоритет: {start_data[priority]}'),
        Format('Статус: {start_data[status]}'),
        Button(Const('Инфо от клиента'), id='client_task', on_click=client_info),
        Button(Const('Редактировать'), id='accept_task', on_click=accept_task, when=is_opened),
        Button(Const('Назначить исполнителя'), id='refuse_task', on_click=refuse_task, when=not_in_archive),
        Button(Const('Закрыть'), id='close_task', on_click=close_task, when=is_in_progress),
        Button(Const('Вернуть в работу'), id='back_to_work', on_click=get_back, when=is_performed),
        Cancel(Const('Назад')),
        state=WorkerTaskSG.main
    ),
)