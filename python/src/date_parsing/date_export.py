import attr_type_constraint
import re
from date_parsing.date_format import DateFormat


@attr_type_constraint.auto_attr_check
class DateExport:

    def __init__(self, year, month, day, bc = False):
        """
        Initialize DateExport with year month and day values
        """
        self.year = year
        self.month = month
        self.day = day
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

    def __sub__(self, o):
        return DateExport(self.year - o.year, self.month - o.month, self.day - o.day)

    def __repr__(self):
        return "{self.day}.{self.month}.{self.year} (BC: {self.BC})".format(self=self)

    def __str__(self):
        return self.__repr__()
