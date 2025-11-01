from django.urls import path
from . import views

app_name = 'shifts'

urlpatterns = [
    path('shift_matrix/', views.shift_matrix_view, name='shift_matrix'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path("salary/", views.salary_view, name="salary_view"),
]