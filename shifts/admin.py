from django.contrib import admin
from .models import Employee, Shift, Holiday


class HolidayInline(admin.TabularInline):
    model = Holiday
    extra = 1  # 追加用の空欄を1つ表示

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days')
    inlines = [HolidayInline]  # インライン追加

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date')
    list_filter = ('employee', 'date')