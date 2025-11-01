from django.db import models

WEEKDAYS = [
    (0, '月'),
    (1, '火'),
    (2, '水'),
    (3, '木'),
    (4, '金'),
    (5, '土'),
    (6, '日'),
]

class ShiftRequirement(models.Model):
    weekday = models.IntegerField(choices=WEEKDAYS, unique=True)
    min_staff = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.get_weekday_display()}: {self.min_staff}人"

SHIFT_TIMES = [
    "9:00-17:00",   # 早番
    "11:00-19:00",  # 中番
    "13:00-21:00",  # 遅番
]

class Employee(models.Model):
    ROLE_CHOICES = [
        ('manager', '正社員'),
        ('staff', '準社'),
        ('part', 'アルバイト'),
    ]
    ROLE_ORDER = {
        'manager': 1,   # 正社員
        'staff': 2,     # 準社
        'part': 3,      # アルバイト
    }

    name = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_days = models.PositiveIntegerField(default=22)  # 月最大勤務日数

    def role_order(self):
        """役職の並び順を返す"""
        return self.ROLE_ORDER.get(self.role, 99)


    def __str__(self):
        # 名前 + 役職 を返すようにする
        return f"{self.name} ({self.get_role_display()})"


class Holiday(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="holidays",
        null=True,   # ← 最初はnull許可
        blank=True   # ← 管理画面で空でもOK
    )
    date = models.DateField()

    def __str__(self):
        return f"{self.employee.name if self.employee else '未設定'}: {self.date}"


class RequestedOff(models.Model):
    employee = models.ForeignKey(Employee, related_name='requested_off_dates', on_delete=models.CASCADE)
    date = models.DateField()


class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    time_range = models.CharField(max_length=20, choices=[(t, t) for t in SHIFT_TIMES], blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.employee.name} - {self.date}"
