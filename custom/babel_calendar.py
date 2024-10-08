from datetime import date
from typing import Dict

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Calendar, CalendarScope
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    CalendarDaysView, CalendarMonthView, CalendarScopeView, CalendarYearsView,
)
from aiogram_dialog.widgets.text import Text
from babel.dates import get_month_names, get_day_names


class RuWeekDay(Text):
    def __init__(self, locale):
        super().__init__()
        self.locale = locale

    async def _render_text(self, data, manager: DialogManager) -> str:
        selected_date: date = data["date"]
        return get_day_names(
            width="short", context='stand-alone', locale=self.locale
        )[selected_date.weekday()].title()


class RuMonth(Text):
    def __init__(self, locale):
        super().__init__()
        self.locale = locale

    async def _render_text(self, data, manager: DialogManager) -> str:
        selected_date: date = data["date"]
        # print("month", selected_date.month)
        return get_month_names(
            'wide', context='stand-alone', locale=self.locale
        )[selected_date.month].title()


class CustomCalendar(Calendar):
    def _init_views(self) -> Dict[CalendarScope, CalendarScopeView]:
        return {
            CalendarScope.DAYS: CalendarDaysView(
                self._item_callback_data, self.config,
                header_text=RuMonth("ru_RU"),
                weekday_text=RuWeekDay("ru_RU"),
                next_month_text=RuMonth("ru_RU") + " >>",
                prev_month_text="<< " + RuMonth("ru_RU"),
            ),
            CalendarScope.MONTHS: CalendarMonthView(
                self._item_callback_data, self.config,
                month_text=RuMonth("ru_RU"),
                this_month_text="[" + RuMonth("ru_RU") + "]",
            ),
            CalendarScope.YEARS: CalendarYearsView(
                self._item_callback_data, self.config,
            ),
        }
