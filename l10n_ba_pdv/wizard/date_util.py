from datetime import datetime, timedelta
from odoo.exceptions import UserError

class DateUtil:

    # date: 29.03.2023 -> return 01.02.2023
    @staticmethod
    def previous_month(date):
        date = date.replace(day=1)
        month = date.month
        year = date.year
        if month == 1:
            date = date.replace(month=12, year=year-1)
        else:
            date = date.replace(month=month-1)
        return date

    @staticmethod
    def begin_of_month(date):
        date = date.replace(day=1)
        return date

    @staticmethod
    def default_date_from():

        #today = 10.03.2023 => 1.01.2023
        start_date = DateUtil.previous_month(datetime.today().date())
        #start_date = DateUtil.previous_month(start_date)
        # 01.01.2023
        return start_date

    @staticmethod
    def default_date_to():

        # today = 10.03.2025 => 01.03.2025
        to_date = DateUtil.begin_of_month(datetime.today().date())

        # 28.02.2025
        return to_date + timedelta(days=-1)

    @staticmethod
    def current_time_str():
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def current_date_str():
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def date_str(date):
        return date.strftime("%d.%m.%Y")