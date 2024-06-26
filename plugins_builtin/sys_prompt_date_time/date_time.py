import enum
import locale

import pendulum
from pydantic import BaseModel

from models.context import Context
from models.system_prompt import SystemPrompt
from plugin_system.abc.sys_prompt import SystemPromptPlugin


class PartOfDay(enum.Enum):
    MORNING = 1
    NOON = 2
    AFTERNOON = 3
    EVENING = 4
    NIGHT = 5


class PartOfDayDeVal(enum.StrEnum):
    MORNING = "Morgend"
    NOON = "Mittag"
    AFTERNOON = "Nachmittag"
    EVENING = "Abend"
    NIGHT = "Nacht"


class Season(enum.Enum):
    SPRING = 1
    SUMMER = 2
    AUTUMN = 3
    WINTER = 4


class SeasonDeVal(enum.StrEnum):
    SPRING = "Frühling"
    SUMMER = "Sommer"
    AUTUMN = "Herbst"
    WINTER = "Winter"


class DateTimeConfigModel(BaseModel):
    locale: str = None  # locale code, if not set system locale is used
    # country: str = "de"
    timezone: str = None  # timezone string, if not set, system timezone is applied
    show_time: bool = True  # locale aware time
    show_date: bool = True  # locale aware date
    show_year_only: bool = False  #
    show_weekday: bool = True  # monday and so on
    show_seasson: bool = True  # spring,summer,autumn,winter
    show_part_of_the_week: bool = True  # weekend/weekday
    show_part_of_the_day: bool = True  # morning/noon/afternoon/evening/night


class DateTimePrompt(SystemPromptPlugin):
    config: DateTimeConfigModel

    async def plugin_setup(self) -> None:
        config = self.pm.get_plugin_config(self.__class__.__name__)
        self.config = DateTimeConfigModel(**config)
        if not self.config.locale:
            self.config.locale = self.get_system_locale()
        pendulum.set_locale(self.config.locale)

    async def generate_system_prompts(self, ctx: Context) -> list[SystemPrompt]:  # noqa: ARG002
        now = pendulum.now()
        # TODO: in the future we should check if its a holiday too but that needs some kind of api to get all the
        #       holidays in the world and a way to determin where we are.
        # TODO: find a better solution then this if else nightmare...

        if self.config.locale == "de":
            return [SystemPrompt(name="DateTime", content=self.result_de(now))]
        return [SystemPrompt(name="DateTime", content=self.result_en(now))]

    def result_en(self, now: pendulum.DateTime) -> str:
        day_type = "weekend" if self.is_weekend(now) else "a weekday"

        return f"It's {now.format('dddd, D. of MMMM YYYY')}. It's {now.format("HH:mm:ss")} o'clock. It's {day_type}"

    def result_de(self, now: pendulum.DateTime) -> str:
        result_list = []
        if self.config.show_weekday:
            result_list.append(f"Heute ist {now.format("dddd")}.")
        if self.config.show_part_of_the_week:
            day_type = "Wir haben Wochenende." if self.is_weekend(now) else "Heute ist ein Wochentag."
            result_list.append(day_type)
        if self.config.show_date:
            if self.config.show_year_only:
                result_list.append(f"Es ist das Jahr {now.format('YYYY')}.")
            else:
                result_list.append(f"Es ist der {now.format('D. MMMM YYYY')}.")
        if self.config.show_seasson:
            season = self.get_season(now)
            result_list.append(f"Zurzeit ist es {SeasonDeVal[season.name].value}.")
        if self.config.show_time:
            result_list.append(f"Wir haben es {now.format("HH:mm")} Uhr.")
        if self.config.show_part_of_the_day:
            day_part = self.get_part_of_the_day(now)
            result_list.append(f"Es ist {PartOfDayDeVal[day_part.name].value}.")

        return " ".join(result_list)

    def is_weekend(self, dt: pendulum.DateTime) -> bool:
        """
        Check if the given datetime falls on a weekend.

        Args:
            now (pendulum.DateTime): The datetime to check.

        Returns:
            bool: True if the datetime falls on a weekend, False otherwise.
        """
        return dt.day_of_week in [6, 5]

    def get_part_of_the_day(self, dt: pendulum.DateTime) -> PartOfDay:
        pod = None
        if self.is_morning(dt):
            pod = PartOfDay.MORNING
        elif self.is_noon(dt):
            pod = PartOfDay.NOON
        elif self.is_afternoon(dt):
            pod = PartOfDay.AFTERNOON
        elif self.is_evening(dt):
            pod = PartOfDay.EVENING
        elif self.is_night(dt):
            pod = PartOfDay.NIGHT
        else:
            pod = None
        return pod

    def is_morning(self, dt: pendulum.DateTime) -> bool:
        start_time = dt.set(hour=5, minute=0, second=0)
        end_time = dt.set(hour=11, minute=0, second=0)
        return start_time <= dt < end_time

    def is_noon(self, dt: pendulum.DateTime) -> bool:
        start_time = dt.set(hour=11, minute=0, second=0)
        end_time = dt.set(hour=13, minute=0, second=0)
        return start_time <= dt < end_time

    def is_afternoon(self, dt: pendulum.DateTime) -> bool:
        start_time = dt.set(hour=13, minute=0, second=0)
        end_time = dt.set(hour=18, minute=0, second=0)
        return start_time <= dt < end_time

    def is_evening(self, dt: pendulum.DateTime) -> bool:
        start_time = dt.set(hour=18, minute=0, second=0)
        end_time = dt.set(hour=22, minute=0, second=0)
        return start_time <= dt < end_time

    def is_night(self, dt: pendulum.DateTime) -> bool:
        start_time = dt.set(hour=22, minute=0, second=0)
        end_time = dt.set(hour=5, minute=0, second=0)
        return start_time <= dt or dt < end_time

    def get_system_locale(self) -> str:
        system_locale = locale.getdefaultlocale()
        return system_locale[0].split("_")[0]

    def get_season(self, dt: pendulum.DateTime) -> Season:
        s = None
        if self.is_spring(dt):
            s = Season.SPRING
        elif self.is_summer(dt):
            s = Season.SUMMER
        elif self.is_autumn(dt):
            s = Season.AUTUMN
        elif self.is_winter(dt):
            s = Season.WINTER
        else:
            s = None
        return s

    def is_spring(self, dt: pendulum.DateTime) -> bool:
        start_date = dt.set(month=3, day=1)
        end_date = dt.set(month=6, day=1)
        return start_date <= dt < end_date

    def is_summer(self, dt: pendulum.DateTime) -> bool:
        start_date = dt.set(month=6, day=1)
        end_date = dt.set(month=9, day=1)
        return start_date <= dt < end_date

    def is_autumn(self, dt: pendulum.DateTime) -> bool:
        start_date = dt.set(month=9, day=1)
        end_date = dt.set(month=12, day=1)
        return start_date <= dt < end_date

    def is_winter(self, dt: pendulum.DateTime) -> bool:
        start_date = dt.set(month=12, day=1)
        end_date = dt.set(month=3, day=1)
        return start_date <= dt or dt < end_date
