import attr_type_constraint


@attr_type_constraint.auto_attr_check
class DateExport:
    year = int
    month = int
    day = int

    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    def __sub__(self, o):
        return DateExport(self.year - o.year, self.month - o.month, self.day - o.day)

    def __repr__(self):
        return "{self.day}.{self.month}.{self.year}".format(self=self)

    def __str__(self):
        return self.__repr__()
