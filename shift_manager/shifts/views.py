from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from .models import Employee, Shift
from datetime import date, timedelta
import calendar
import random
import openpyxl
import csv
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

WEEK_NAMES = ['月', '火', '水', '木', '金', '土', '日']
SHIFT_TIMES = ["9:00-17:00", "11:00-19:00", "13:00-21:00"]

def index(request):
    return render(request, 'index.html')


def shift_matrix_view(request):
    today = date.today()

    # 年月取得
    if request.method == "POST":
        year = int(request.POST.get('year', today.year))
        month = int(request.POST.get('month', today.month))
    else:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

    # 月の日付リスト
    num_days = calendar.monthrange(year, month)[1]
    month_days = [date(year, month, d) for d in range(1, num_days + 1)]
    header_days = [{'date': d, 'weekday_name': WEEK_NAMES[d.weekday()], 'is_weekend': d.weekday() >= 5} for d in month_days]

    # 前月・次月
    prev_month, prev_year = (month-1, year) if month > 1 else (12, year-1)
    next_month, next_year = (month+1, year) if month < 12 else (1, year+1)

    # 従業員
    employees = list(Employee.objects.all())
    employees.sort(key=lambda e: e.role_order())

    # ==============================
    # 自動生成ボタン押下時
    # ==============================
    if request.method == 'POST' and 'auto_generate' in request.POST:
        Shift.objects.filter(date__year=year, date__month=month).delete()

        emp_last_worked = {emp.id: None for emp in employees}
        emp_consecutive = {emp.id: 0 for emp in employees}
        emp_assigned_count = {emp.id: 0 for emp in employees}

        min_daily = 6
        max_daily = 10
        MAX_CONSECUTIVE_DAYS = 5

        # ✅ 日付を順番に処理
        for d in month_days:
            available_emps = []

            for emp in employees:
                # 希望休は休み
                if d in {off.date for off in emp.requested_off_dates.all()}:
                    continue

                last_day = emp_last_worked[emp.id]
                consecutive = emp_consecutive[emp.id]

                # 昨日も働いていたら+1、そうでなければリセット
                if last_day == d - timedelta(days=1):
                    consecutive += 1
                else:
                    consecutive = 1

                # 6連勤防止
                if consecutive > MAX_CONSECUTIVE_DAYS:
                    continue

                # まだOKなら候補へ
                available_emps.append(emp)

            # 土日は少し多めに
            if d.weekday() >= 5:
                min_daily_for_day = min_daily + 2
                max_daily_for_day = max_daily + 2
            else:
                min_daily_for_day = min_daily
                max_daily_for_day = max_daily

            # ランダムに選ぶ
            if available_emps:
                num_to_assign = min(len(available_emps), random.randint(min_daily_for_day, max_daily_for_day))
                chosen_emps = random.sample(available_emps, num_to_assign)
            else:
                chosen_emps = []

            # ✅ 出勤登録 & カウント更新
            for emp in chosen_emps:
                Shift.objects.create(employee=emp, date=d, time_range=random.choice(SHIFT_TIMES))
                emp_assigned_count[emp.id] += 1

                if emp_last_worked[emp.id] == d - timedelta(days=1):
                    emp_consecutive[emp.id] += 1
                else:
                    emp_consecutive[emp.id] = 1
                emp_last_worked[emp.id] = d

            # ✅ 働かなかった人は連勤リセット
            chosen_ids = {e.id for e in chosen_emps}
            for emp in employees:
                if emp.id not in chosen_ids:
                    if emp_last_worked[emp.id] and emp_last_worked[emp.id] == d - timedelta(days=1):
                        emp_consecutive[emp.id] = 0

        return redirect(f"{reverse('shifts:shift_matrix')}?year={year}&month={month}")

    # ==============================
    # シフト表作成
    # ==============================
    shift_matrix = []
    for emp in employees:
        emp_shift_qs = emp.shifts.filter(date__month=month, date__year=year)
        total_hours = 0
        for s in emp_shift_qs:
            if s.time_range:
                start, end = s.time_range.split('-')
                sh, sm = map(int, start.split(':'))
                eh, em = map(int, end.split(':'))
                total_hours += (eh + em/60) - (sh + sm/60)

        emp_shifts = {s.date: s.time_range for s in emp_shift_qs}
        emp_row = {
            'id': emp.id,
            'name': emp.name,
            'role': emp.get_role_display(),
            'work_hours': total_hours,
            'shifts': []
        }

        for d in month_days:
            emp_row['shifts'].append({
                'date': d,
                'is_weekend': d.weekday() >= 5,
                'time_range': emp_shifts.get(d, '')
            })

        shift_matrix.append(emp_row)

    attendance_counts = {
        d: Shift.objects.filter(date=d).exclude(time_range='').count()
        for d in month_days
    }

    context = {
        'shift_matrix': shift_matrix,
        'month_days': header_days,
        'year': year,
        'month': month,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'attendance_counts': attendance_counts,
    }

    return render(request, 'shifts/shift_matrix.html', context)


# =========================
# Excel出力
# =========================
def export_excel(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    num_days = calendar.monthrange(year, month)[1]
    month_days = [date(year, month, d) for d in range(1, num_days + 1)]
    employees = sorted(Employee.objects.all(), key=lambda e: e.role_order())

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{year}年{month}月シフト"

    headers = ["名前", "役職"] + [f"{d.day}日({WEEK_NAMES[d.weekday()]})" for d in month_days]
    ws.append(headers)

    for emp in employees:
        row = [emp.name, emp.get_role_display()]
        emp_shifts = {s.date: s.time_range for s in emp.shifts.filter(date__month=month, date__year=year)}
        for d in month_days:
            row.append(emp_shifts.get(d, "休"))
        ws.append(row)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename=shift_{year}_{month}.xlsx'
    wb.save(response)
    return response


# =========================
# CSV出力
# =========================
def export_csv(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    num_days = calendar.monthrange(year, month)[1]
    month_days = [date(year, month, d) for d in range(1, num_days + 1)]
    employees = sorted(Employee.objects.all(), key=lambda e: e.role_order())

    # UTF-8 BOM付き
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename=shift_{year}_{month}.csv'
    response.write('\ufeff')  # BOMを追加

    writer = csv.writer(response, lineterminator='\n')

    # ヘッダ行
    headers = ["名前", "役職"] + [f"{d.day}日({WEEK_NAMES[d.weekday()]})" for d in month_days]
    writer.writerow(headers)

    # データ行
    for emp in employees:
        row = [emp.name, emp.get_role_display()]
        emp_shifts = {s.date: s.time_range for s in emp.shifts.filter(date__month=month, date__year=year)}
        for d in month_days:
            row.append(emp_shifts.get(d, "休"))
        writer.writerow(row)

    return response



# =========================
# 給与グラフ表示
# =========================
def salary_view(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    employees = Employee.objects.all()
    chart_base64 = None
    hourly_rates = {}

    if request.method == "POST":
        for emp in employees:
            rate_str = request.POST.get(f"hourly_{emp.id}", "")
            try:
                emp.hourly_rate = int(float(rate_str))
            except ValueError:
                emp.hourly_rate = 0
            emp.save()

        employees = Employee.objects.all()

        names, salaries = [], []

        for emp in employees:
            total_hours = 0
            emp_shifts = emp.shifts.filter(date__year=year, date__month=month)
            for s in emp_shifts:
                if s.time_range:
                    start, end = s.time_range.split('-')
                    sh, sm = map(int, start.split(':'))
                    eh, em = map(int, end.split(':'))
                    total_hours += (eh + em/60) - (sh + sm/60)
            salary = int(round(float(total_hours) * float(emp.hourly_rate or 0)))
            names.append(emp.name)
            salaries.append(salary)

        plt.rcParams['font.family'] = 'Meiryo'
        plt.figure(figsize=(8, 4))
        bars = plt.barh(names, salaries, color="#ffa94d")

        plt.title(f"{year}年{month}月の給与", fontsize=14)
        plt.xlabel("金額（円）", fontsize=12)
        plt.yticks(rotation=0, ha="right")

        for bar, value in zip(bars, salaries):
            plt.text(value + 1000, bar.get_y() + bar.get_height()/2,
                     f"{int(value):,}円", va='center', fontsize=10)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_base64 = base64.b64encode(buf.read()).decode()
        buf.close()
        plt.close()

    for emp in employees:
        if getattr(emp, 'hourly_rate', None) is not None:
            try:
                hourly_rates[emp.id] = int(round(emp.hourly_rate))
            except Exception:
                hourly_rates[emp.id] = emp.hourly_rate
        else:
            hourly_rates[emp.id] = ""

    return render(request, "shifts/salary_view.html", {
        "employees": employees,
        "chart": chart_base64,
        "year": year,
        "month": month,
        "hourly_rates": hourly_rates,
    })

