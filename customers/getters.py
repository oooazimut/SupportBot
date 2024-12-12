from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId


async def customer_preview_getter(dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data["finished"] = True
    customer_id = dialog_manager.event.from_user.id
    customer_name = dialog_manager.find("cust_name_input").get_value()
    customer_phone = dialog_manager.find("cust_phone_input").get_value()
    customer_object = dialog_manager.find("cust_object_input").get_value()

    dialog_manager.dialog_data["customer"] = {
        "id": customer_id,
        "name": customer_name,
        "phone": customer_phone,
        "object": customer_object,
    }
    return dialog_manager.dialog_data["customer"]


async def task_preview_getter(dialog_manager: DialogManager, **kwargs):
    task = dialog_manager.dialog_data.get("task", {})

    media_type = task.get("media_type", "").split(",")
    media_id = task.get("media_id", "").split(",")
    index = await dialog_manager.find("customer_video_scroll").get_page()
    media = (
        MediaAttachment(media_type[index], file_id=MediaId(media_id[index]))
        if task.get('media_id') 
        else None
    )
    pages = len(media_id)
    return {
        "task": task,
        "pages": pages,
        "media": media,
    }
