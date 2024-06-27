import operator

from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, Back, Radio, Button, Column
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Jinja, Format

from getters.task import priority_getter, result_getter, entitites_getter, slaves_getter, act_getter, \
    agreementers_getter
from handlers.task import (
    next_or_end, CANCEL_EDIT, task_description_handler,
    on_priority, ent_name_handler, on_confirm, on_entity, on_slave, on_start, to_entity, to_phone, to_title,
    to_description, cancel_edit, to_slave, to_priority, on_act, to_act, on_agreementer, to_agreement
)
from states import TaskCreating

create_task_dialog = Dialog(
    Window(
        Const('Выбор объекта. Для получение объекта/объектов введите его название или хотя бы часть.'),
        MessageInput(ent_name_handler, content_types=[ContentType.TEXT]),
        Back(Const('Назад')),
        CANCEL_EDIT,
        state=TaskCreating.sub_entity
    ),
    Window(
        Const('Найденные объекты:'),
        Column(
            Radio(
                Format('🔘 {item[name]}'),
                Format('⚪️ {item[name]}'),
                id='choose_entity',
                item_id_getter=lambda item: item['ent_id'],
                items='entities',
                on_click=on_entity
            ),
        ),
        Button(Const('Подтвердить'), id='confirm_entity', on_click=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        state=TaskCreating.entities,
        getter=entitites_getter
    ),
    Window(
        Const('Ваш номер телефона:'),
        TextInput(id='phone_input', on_success=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_phone
    ),
    Window(
        Const('Тема обращения?'),
        TextInput(id='title_input', on_success=next_or_end),
        CANCEL_EDIT,
        Back(Const('Назад')),
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_title
    ),
    Window(
        Const('Опишите вашу проблему. Это может быть текстовое, голосовое, видеосообщение или картинка.'),
        MessageInput(task_description_handler, content_types=[ContentType.ANY]),
        Back(Const('Назад')),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_description
    ),
    Window(
        Const('Выбор приоритета:'),
        Radio(
            Format('🔘 {item[0]}'),
            Format('⚪️ {item[0]}'),
            id='ch_prior',
            item_id_getter=operator.itemgetter(1),
            items='priorities',
            on_click=on_priority
        ),
        Button(Const('Подтвердить'), id='confirm_priority', on_click=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        getter=priority_getter,
        state=TaskCreating.priority
    ),
    Window(
        Const('Необходимость акта от исполнителя:'),
        Radio(
            Format('🔘 {item[0]}'),
            Format('⚪️ {item[0]}'),
            id='act_nssr',
            item_id_getter=lambda x: x[1],
            items='act_nssr',
            on_click=on_act
        ),
        Button(Const('Подтвердить'), id='confirm_act', on_click=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        getter=act_getter,
        state=TaskCreating.act
    ),
    Window(
        Const('Назначить работника'),
        Column(
            Radio(
                Format('🔘 {item[username]}'),
                Format('⚪️ {item[username]}'),
                id='choose_slave',
                item_id_getter=lambda item: item['userid'],
                items='slaves',
                on_click=on_slave
            ),
        ),
        Button(Const('Подтвердить'), id='confirm_slave', on_click=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        state=TaskCreating.slave,
        getter=slaves_getter
    ),
    Window(
        Const('Если нужно согласование, выберите с кем:'),
        Column(
            Radio(
                Format('🔘 {item}'),
                Format('⚪️ {item}'),
                id='agreementers',
                item_id_getter=lambda item: item,
                items='agreementers',
                on_click=on_agreementer
            )
        ),
        Button(Const('Подтвердить'), id='confirm_agreementer', on_click=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        state=TaskCreating.agreements,
        getter=agreementers_getter
    ),
    Window(
        Jinja('''Ваша заявка:

        <b>Объект</b>: {{entity if entity else ''}}
        <b>Телефон</b>: {{phone if phone else ''}}
        <b>Тема</b>: {{title if title else ''}}
        <b>Описание</b>: {{description if description else ''}}
        <b>Приоритет</b>: {{priority if priority else ''}}
        <b>Работник</b>: {{username if username else ''}}
        <b>Акт</b>: {{'Да' if act else 'Нет'}}
        <b>Согласование</b>: {{agreement if agreement else ''}}
        '''),
        DynamicMedia('media', when=F['media']),
        Button(Const('Сохранить'), id='confirm_creating', on_click=on_confirm),
        Button(Const('Изменить объект'), id='to_entity', on_click=to_entity),
        Button(Const('Изменить телефон'), id='to_phone', on_click=to_phone),
        Button(Const('Изменить Тему'), id='to_title', on_click=to_title),
        Button(Const('Изменить приоритет'), id='to_priority', on_click=to_priority),
        Button(Const('Необходимость акта'), id='to_act', on_click=to_act),
        Button(Const('Изменить описание'), id='to_description', on_click=to_description),
        Button(Const('Изменить исполнителя'), id='to_slave', on_click=to_slave),
        Button(Const('Необходимость согласования'), id='to_agreement', on_click=to_agreement),
        Button(Const('Отмена'), id='cancel_edit', on_click=cancel_edit),
        state=TaskCreating.preview,
        getter=result_getter,
        parse_mode='html'
    ),
    Window(
        Const('Объектов не найдено'),
        SwitchTo(Const('Попробовать ещё раз'), id='reenter_entity', state=TaskCreating.sub_entity),
        SwitchTo(Const('Продолжить без объекта'), id='without_entity', state=TaskCreating.enter_phone),
        CANCEL_EDIT,
        state=TaskCreating.empty_entities
    ),
    on_start=on_start,
)
