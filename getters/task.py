from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

import config
from db import empl_service, task_service


async def priority_getter(dialog_manager: DialogManager, **kwargs):
    priorities = [
        ('низкий', ' '),
        ('высокий', '\U0001F525')
    ]
    return {
        'priorities': priorities
    }


async def act_getter(dialog_manager: DialogManager, **kwargs):
    act_nesessary = [
        ('с актом', 1),
        ('без акта', 0)
    ]
    return {'act_nssr': act_nesessary}


async def entitites_getter(dialog_manager: DialogManager, **kwargs):
    entities = dialog_manager.dialog_data['entities']
    return {
        'entities': entities
    }


async def slaves_getter(dialog_manager: DialogManager, **kwargs):
    slaves = empl_service.get_employees_by_position('worker')
    return {
        'slaves': slaves
    }


async def agreementers_getter(dialog_manager: DialogManager, **k):
    return {'agreementers': config.AGREEMENTERS}


async def result_getter(dialog_manager: DialogManager, **kwargs):
    data: dict = dialog_manager.dialog_data['task']

    media = None
    mediatype = data.get('media_type')
    mediaid = data.get('media_id')
    if mediatype and mediaid:
        media = MediaAttachment(mediatype, file_id=MediaId(mediaid))

    phone = dialog_manager.find('phone_input').get_value()
    if phone != 'None':
        data['phone'] = phone

    title = dialog_manager.find('title_input').get_value()
    if title != 'None':
        data['title'] = title

    data.update({'media': media})
    dialog_manager.dialog_data['task'] = data
    dialog_manager.dialog_data['finished'] = True
    return data


async def performed_getter(dialog_manager: DialogManager, **kwargs):
    task = task_service.get_task(dialog_manager.start_data['taskid'])[0]
    performed_counter = len(task_service.get_tasks_by_status('выполнено'))
    task.update({'counter': performed_counter})
    return task
