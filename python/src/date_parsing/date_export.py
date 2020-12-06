from utilities import attr_type_constraint, utils
from utilities.runtime_constants import RuntimeConstants
import re
from date_parsing.date_format import DateFormat
from datetime import datetime
from collections import namedtuple
import numpy as np

@attr_type_constraint.auto_attr_check
class DateExport:

    def __init__(self, year, month, day, bc = False):
        """
        Initialize DateExport with year month and day values
        """
        if month == "None" or month is None:
            self.month = None
        else:
            self.month = month

        if day == "None" or day is None:
            self.day = None
        else:
            self.day = day

        self.year = year
        self.BC = bc

    @classmethod
    def from_format(cls, text, form = DateFormat):
        """
        Initialize DateExport with text in specified format
        """
        if form == DateFormat.AS_TEXT:
            (year, month, day) = cls.parse_as_text_format(cls, text)
            return cls(year, month, day)
        elif form == DateFormat.YEAR_ONLY:
            (year, month, day) = cls.parse_as_yearonly_format(cls, text)
            return cls(year, month, day)
        elif form == DateFormat.TXTMONTH_AND_YEAR:
            (year, month, day) = cls.parse_as_txtmonth_and_year_format(cls, text)
            return cls(year, month, day)
        elif form == DateFormat.TXTMONTH_FULL:
            (year, month, day) = cls.parse_as_txtmonth_full_format(cls, text)
            return cls(year, month, day)

    @staticmethod
    def parse_as_yearonly_format(self, text):
        # 1874
        exp_year = int(text)
        return exp_year, None, None

    @staticmethod
    def parse_as_txtmonth_and_year_format(self, text):
        # July 1874
        match = re.search("([a-zA-Z]+)(?:\W+|,)(\d{1,4})", text)
        exp_year = int(match[2])
        exp_month = self.month_to_num(match[1])

        return exp_year, exp_month, None

    @staticmethod
    def parse_as_txtmonth_full_format(self, text):
        # 14 July 1874
        match = re.search("(\d{1,2})\W+([a-zA-Z]+)\W+(\d{1,4})", text)
        exp_day = int(match[1])
        exp_month = self.month_to_num(match[2])
        exp_year = int(match[3])

        return exp_year, exp_month, exp_day

    @staticmethod
    def parse_as_text_format(self, text):
        match = re.search("([a-zA-Z]+) (\d{1,2}), (\d{4})", text)

        exp_year = int(match[3])
        exp_day = int(match[2])
        exp_month = self.month_to_num(match[1])

        return exp_year, exp_month, exp_day

    @staticmethod
    def month_to_num(month_name = str):
        return {
            'january': 1,
            'february': 2,
            'march': 3,
            'april': 4,
            'may': 5,
            'june': 6,
            'july': 7,
            'august': 8,
            'september': 9,
            'october': 10,
            'november': 11,
            'december': 12
        }[month_name.lower()]

    @staticmethod
    def is_correct_age(birth, death):
        if birth is None:
            return False

        if death == "alive":
            return True

        if not birth.BC and not death.BC:
            return birth.year < death.year and (death.year - birth.year < 110)
        elif birth.BC and not death.BC:
            return True and (death.year + birth.year < 110)
        elif not birth.BC and death.BC:
            return False
        elif birth.BC and death.BC:
            return birth.year > death.year and (birth.year - death.year < 110)

        return False

    @staticmethod
    def could_meet(b1,d1,b2,d2):

        parse = re.search(r"(.+?)\.(.+?)\.(\d+)\W?(BC)?", b1)
        b1_date = DateExport(parse[3], 12 if parse[2] == "None" else parse[2], 31 if parse[1] == "None" else parse[1], parse[4] == "BC")

        if d1 == "alive":
            d1_date = DateExport(RuntimeConstants.CURRENT_YEAR, 12, 31)
        else:
            parse = re.search(r"(.+?)\.(.+?)\.(\d+)\W?(BC)?", d1)
            d1_date = DateExport(parse[3], 12 if parse[2] == "None" else parse[2], 31 if parse[1] == "None" else parse[1], parse[4] == "BC")

        parse = re.search(r"(.+?)\.(.+?)\.(\d+)\W?(BC)?", b2)
        b2_date = DateExport(parse[3], 12 if parse[2] == "None" else parse[2], 31 if parse[1] == "None" else parse[1], parse[4] == "BC")

        if d2 == "alive":
            d2_date = DateExport(RuntimeConstants.CURRENT_YEAR, 12, 31)
        else:
            parse = re.search(r"(.+?)\.(.+?)\.(\d+)\W?(BC)?", d2)
            d2_date = DateExport(parse[3], 12 if parse[2] == "None" else parse[2], 31 if parse[1] == "None" else parse[1], parse[4] == "BC")

        Range = namedtuple('Range', ['start', 'end'])
        r1 = Range(start=b1_date.__iso8601_str__(), end=d1_date.__iso8601_str__())
        r2 = Range(start=b2_date.__iso8601_str__(), end=d2_date.__iso8601_str__())

        latest_start = max(r1.start, r2.start)
        earliest_end = min(r1.end, r2.end)
        delta = (earliest_end - latest_start)
        overlap = max(0, delta)

        return overlap > 0

    def __iso8601_str__(self):
        string = ("-" if self.BC else "+") + "%04d-%02d-%02dT00:00:00Z" % (int(self.year), int(self.month), int(self.day))
        date_str = string.strip()
        if date_str[0] == '+':
            date_str = date_str[1:]
        date_str = date_str.split('-00', maxsplit=1)[0]
        dt = np.datetime64(date_str)
        return dt.astype('<M8[s]').astype(np.int64)
    def __sub__(self, o):
        return DateExport(self.year - o.year, self.month - o.month, self.day - o.day)

    def __repr__(self):
        return "{self.day}.{self.month}.{self.year} (BC: {self.BC})".format(self=self)

    def __str__(self):
        return self.__repr__()
