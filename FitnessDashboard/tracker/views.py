import base64
import datetime
import io
from collections import defaultdict
from io import BytesIO
from typing import Any
import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.db.models import Count
from django.http import FileResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import (
    BodyMeasure,
    Exercise,
    Meal,
    Nutrition,
    TrainingHistory,
    TrainingPlan,
    YoutubeChannel,
    WeeklySplit,
)


# =============================================================================
# Constants
# =============================================================================

CHART_COLORS = [
    "#069a8e",
    "#f4dba0",
]

BODY_MEASURE_FIELDS = [
    "weight",
    "waist",
    "chest",
    "arm_left",
    "arm_right",
]

BODY_MEASURE_ROW_CONFIG = [
    {
        "label": "Weight",
        "field": "weight",
        "unit": "kg",
        "icon": "tracker/svg/weight.svg",
        "icon_name": "weight.svg",
        "success_if": "decrease",
        "flip_icon": False,
    },
    {
        "label": "Waist",
        "field": "waist",
        "unit": "cm",
        "icon": "tracker/svg/waist.svg",
        "icon_name": "waist.svg",
        "success_if": "decrease",
        "flip_icon": False,
    },
    {
        "label": "Chest",
        "field": "chest",
        "unit": "cm",
        "icon": "tracker/svg/chest.svg",
        "icon_name": "chest.svg",
        "success_if": "increase",
        "flip_icon": False,
    },
    {
        "label": "Arm left",
        "field": "arm_left",
        "unit": "cm",
        "icon": "tracker/svg/arm.svg",
        "icon_name": "arm.svg",
        "success_if": "increase",
        "flip_icon": True,
    },
    {
        "label": "Arm right",
        "field": "arm_right",
        "unit": "cm",
        "icon": "tracker/svg/arm.svg",
        "icon_name": "arm.svg",
        "success_if": "increase",
        "flip_icon": False,
    },

]


NUTRITION_CONFIG = [
    {
        "label": "Water",
        "value_field": "water_l",
        "aim_field": "water_l_aim",
        "unit": "l",
        "icon": "tracker/svg/water.svg",
        "icon_name": "water.svg",
    },
    {
        "label": "Protein",
        "value_field": "protein_g",
        "aim_field": "protein_g_aim",
        "unit": "g",
        "icon": "tracker/svg/milkshake.svg",
        "icon_name": "milkshake.svg",
    },
    {
        "label": "Calories",
        "value_field": "calories_kcal",
        "aim_field": "calories_kcal_aim",
        "unit": "kcal",
        "icon": "tracker/svg/fire.svg",
        "icon_name": "fire.svg",
    },
    {
        "label": "Sleep",
        "value_field": "sleep_h",
        "aim_field": "sleep_h_aim",
        "unit": "h",
        "icon": "tracker/svg/sleep.svg",
        "icon_name": "sleep.svg",
    },
]


# =============================================================================
# PDF Export Helper
# =============================================================================


def render_pdf(request, template_name, context, filename):
    html_string = render_to_string(
        template_name,
        context,
        request=request,
    )

    pdf_bytes = HTML(
        string=html_string,
        base_url=request.build_absolute_uri("/"),
    ).write_pdf()

    pdf_buffer = BytesIO(pdf_bytes)

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )


# =============================================================================
# Plot Helper Functions
# =============================================================================


def figure_to_base64(fig):
    buffer = io.BytesIO()

    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)

    image_png = buffer.getvalue()

    buffer.close()
    plt.close(fig)

    return base64.b64encode(image_png).decode("utf-8")


def generate_line_chart(
    plot_list,
    dates,
    measures_1,
    icon,
    title,
    subtitle,
    label,
    measure_2=None,
    label_2=None,
):
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        dates,
        measures_1,
        marker="o",
        linestyle="-",
        label=label,
        color=CHART_COLORS[0],
    )

    if measure_2 is not None and label_2 is not None:
        ax.plot(
            dates,
            measure_2,
            marker="o",
            linestyle="--",
            label=label_2,
            color=CHART_COLORS[1],
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("Measurement")
    ax.legend()
    ax.grid(True)

    fig.autofmt_xdate()

    plot_list.append(
        {
            "title": title,
            "subtitle": subtitle,
            "icon": icon,
            "image": figure_to_base64(fig),
            "alt": f"Plot | {title}",
        }
    )


def donut_chart_generator(values, labels, title=""):
    fig, ax = plt.subplots(figsize=(5, 5))

    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=CHART_COLORS,
        textprops={
            "fontsize": 14,
        },
        wedgeprops={
            "width": 0.35,
            "edgecolor": "white",
        },
    )

    ax.set_title(title)
    ax.axis("equal")

    return fig


# =============================================================================
# Dashboard Data Functions
# =============================================================================

def get_user_data(request):
    user = request.user

    if not user.is_authenticated:
        return None

    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }

def get_current_date():
    today = datetime.date.today()
    calendar_week = today.isocalendar().week

    return f"CW {calendar_week:02d} | {today.strftime('%d.%m.%Y')}"


def get_current_salute():
    current_hour = datetime.datetime.now().hour

    if 5 <= current_hour < 12:
        return "Good Morning"
    elif 12 <= current_hour < 17:
        return "Welcome back"
    elif 17 <= current_hour < 22:
        return "Good Evening"
    else:
        return "Hello"


def calc_nutrition_difference(value, aim):
    if value is None or aim is None:
        return None

    return round(value - aim, 2)


def get_current_nutrition_data():
    latest_nutrition = Nutrition.objects.order_by("date").last()

    if latest_nutrition is None:
        return {
            "latest_nutrition": None,
            "nutrition_rows": [],
        }

    nutrition_rows = []

    for row in NUTRITION_CONFIG:
        value_field = row["value_field"]
        aim_field = row["aim_field"]

        value = getattr(latest_nutrition, value_field)
        aim = getattr(latest_nutrition, aim_field)

        difference = calc_nutrition_difference(value, aim)

        nutrition_rows.append(
            {
                "label": row["label"],
                "unit": row["unit"],
                "icon": row["icon"],
                "icon_name": row["icon_name"],
                "value": value,
                "aim": aim,
                "difference": difference,
                "date": latest_nutrition.date,
            }
        )

    return {
        "latest_nutrition": latest_nutrition,
        "nutrition_rows": nutrition_rows,
    }



def get_current_weekly_split():
    today = datetime.date.today()

    weekly_split = (
        WeeklySplit.objects
        .filter(date__lte=today)
        .order_by("-date")
        .first()
    )

    if weekly_split is None:
        return None

    days = []

    for day_number in range(1, 8):
        date = weekly_split.date + datetime.timedelta(days=day_number - 1)
        training_plan = getattr(weekly_split, f"day_{day_number}")

        days.append({
            "date": date,
            "weekday": date.strftime("%a").upper(),
            "training_plan": training_plan,
            "training_name": (
                training_plan.training_program
                if training_plan
                else "Rest Day"
            ),
            "is_today": date == today,
        })

    return {
        "title": weekly_split.title,
        "start_date": weekly_split.date,
        "end_date": weekly_split.date + datetime.timedelta(days=6),
        "days": days,
    }


def get_daily_meal_suggestions():

    today = datetime.date.today()

    rng = random.Random(today.toordinal())

    all_meals = (
        Meal.objects
        .order_by("category", "id")
    )

    meal_dict = {
        "breakfast": [],
        "lunch": [],
        "snack": [],
        "dinner": [],
    }


    for meal in all_meals:
        if meal.category in meal_dict:
            meal_dict[meal.category].append(meal)

    return {
        "breakfast": rng.choice(meal_dict["breakfast"]) if meal_dict["breakfast"] else None,
        "lunch": rng.choice(meal_dict["lunch"]) if meal_dict["lunch"] else None,
        "snack": rng.choice(meal_dict["snack"]) if meal_dict["snack"] else None,
        "dinner": rng.choice(meal_dict["dinner"]) if meal_dict["dinner"] else None,
    }



def get_exercise_types_as_donut_chart():
    training_type_rows = (
        TrainingHistory.objects
        .exclude(training_type__isnull=True)
        .exclude(training_type="")
        .values("training_type")
        .annotate(count=Count("id"))
        .order_by("training_type")
    )

    labels = [row["training_type"] for row in training_type_rows]
    values = [row["count"] for row in training_type_rows]

    if not values:
        return None

    total_training_sessions = sum(values)

    fig = donut_chart_generator(
        values=values,
        labels=labels,
    )

    return {
        "image": figure_to_base64(fig),
        "alt": (
            "Donut chart showing the percentage distribution "
            "of all recorded training types."
        ),
        "labels": labels,
        "values": values,
        "total_training_sessions": total_training_sessions,
    }



def get_days_trained_data():
    training_history_entries = TrainingHistory.objects.order_by("date")
    total_training_days = training_history_entries.count()

    first_training_history_entry = training_history_entries.first()

    if first_training_history_entry is None:
        return None

    today = datetime.date.today()

    days_since_first_record = (today - first_training_history_entry.date).days + 1
    days_without_training = days_since_first_record - total_training_days

    training_percentage = round((total_training_days / days_since_first_record) * 100)

    values = [
        total_training_days,
        days_without_training,
    ]

    labels = [
        "days with training",
        "days without training",
    ]

    title = (
        f"{total_training_days} training days out of "
        f"{days_since_first_record} days since "
        f"{first_training_history_entry.date.strftime('%b. %d, %Y')}"
    )

    fig = donut_chart_generator(values, labels, title)

    return {
        "title": "Days Trained",
        "image": figure_to_base64(fig),
        "alt": (
            f"Donut chart showing {total_training_days} training days "
            f"out of {days_since_first_record} days since the first training record."
        ),
        "total_training_days": total_training_days,
        "days_since_first_record": days_since_first_record,
        "first_training_day": first_training_history_entry,
        "days_without_training": days_without_training,
        "training_percentage": training_percentage,
    }


def get_average_training_days_per_week_data():
    training_history_entries = TrainingHistory.objects.order_by("date")
    first_training_history_entry = training_history_entries.first()

    if first_training_history_entry is None:
        return None

    today = datetime.date.today()

    total_training_days = training_history_entries.values("date").distinct().count()
    days_since_first_record = (today - first_training_history_entry.date).days + 1
    weeks_since_first_record = days_since_first_record / 7

    average_training_days = round(total_training_days / weeks_since_first_record, 1)
    average_days_without_training = round(7 - average_training_days, 1)

    values = [
        average_training_days,
        average_days_without_training,
    ]

    labels = [
        "avg. days per week\nwith training",
        "avg. days per week\nwithout training",
    ]

    title = f"{average_training_days} training days per week on average"

    fig = donut_chart_generator(values, labels, title)

    return {
        "title": "Average Training Days per Week",
        "image": figure_to_base64(fig),
        "alt": (
            f"Donut chart showing an average of "
            f"{average_training_days} training days per week."
        ),
        "average_training_days": average_training_days,
        "average_days_without_training": average_days_without_training,
        "weeks_since_first_record": round(weeks_since_first_record, 1),
    }


def get_body_measure_by_position(position):
    queryset = BodyMeasure.objects.order_by("date")

    def search_for_valid_entry(field_name, reverse=False):
        ordered_queryset = queryset.reverse() if reverse else queryset

        for measure in ordered_queryset:
            value = getattr(measure, field_name)

            if value is not None:
                return {
                    "value": value,
                    "date": measure.date,
                }

        return {
            "value": None,
            "date": None,
        }

    if position == 0:
        measures = queryset.first()
        reverse = False
    elif position == -1:
        measures = queryset.last()
        reverse = True
    else:
        raise ValueError(
            "position must be 0 for the first entry or -1 for the last entry"
        )

    if measures is None:
        return None

    statistics: dict[str, Any] = {
        "date": measures.date,
    }

    for field in BODY_MEASURE_FIELDS:
        value = getattr(measures, field)
        value_date = measures.date

        if value is None:
            valid_entry = search_for_valid_entry(field, reverse=reverse)
            value = valid_entry["value"]
            value_date = valid_entry["date"]

        statistics[field] = value
        statistics[f"{field}_date"] = value_date

    return statistics


def calc_body_measure_difference(first_measures, latest_measures, field_name):
    first_value = first_measures[field_name]
    latest_value = latest_measures[field_name]

    if first_value is None or latest_value is None:
        return None

    return round(latest_value - first_value, 2)


def get_success_class(difference, success_if):
    if difference is None:
        return ""

    if success_if == "decrease" and difference <= 0:
        return "value-success"

    if success_if == "increase" and difference > 0:
        return "value-success"

    return "value-fail"


def get_body_measure_improvement_data():
    first_measures = get_body_measure_by_position(0)
    latest_measures = get_body_measure_by_position(-1)

    if first_measures is None or latest_measures is None:
        return None

    improvement_values = {
        "date": latest_measures["date"],
    }

    for field in BODY_MEASURE_FIELDS:
        improvement_values[field] = calc_body_measure_difference(
            first_measures,
            latest_measures,
            field,
        )

    measure_rows = []

    for row in BODY_MEASURE_ROW_CONFIG:
        field = row["field"]
        difference = improvement_values[field]

        measure_rows.append(
            {
                "label": row["label"],
                "unit": row["unit"],
                "icon": row["icon"],
                "icon_name": row["icon_name"],
                "flip_icon": row["flip_icon"],
                "first_value": first_measures[field],
                "first_date": first_measures[f"{field}_date"],
                "latest_value": latest_measures[field],
                "latest_date": latest_measures[f"{field}_date"],
                "difference": difference,
                "success_class": get_success_class(
                    difference,
                    row["success_if"],
                ),
            }
        )

    return {
        "first_measures": first_measures,
        "latest_measures": latest_measures,
        "body_measure_improvement": improvement_values,
        "measure_rows": measure_rows,
    }


def get_youtube_channels():
    youtube_channel_objects = YoutubeChannel.objects.all()

    youtube_channels = []

    for channel in youtube_channel_objects:
        channel_data = {
            "youtube_channel_name": channel.youtube_channel_name,
            "youtube_channel_id": channel.youtube_channel_id[2:],
        }

        youtube_channels.append(channel_data)

    return youtube_channels



# =============================================================================
# Measurement Data Functions
# =============================================================================


def get_body_measure_plots():
    body_measures = BodyMeasure.objects.order_by("date")

    dates = []
    weights = []
    waists = []
    arm_left = []
    arm_right = []
    chest = []

    for entry in body_measures:
        dates.append(entry.date)
        weights.append(entry.weight)
        waists.append(entry.waist)
        arm_left.append(entry.arm_left)
        arm_right.append(entry.arm_right)
        chest.append(entry.chest)

    plots = []

    generate_line_chart(
        plots,
        dates,
        weights,
        "weight",
        "Weight Development",
        "fight gravity",
        "Weight in kg",
    )

    generate_line_chart(
        plots,
        dates,
        waists,
        "waist",
        "Waist Development",
        "hips don't lie",
        "Waist in cm",
    )

    generate_line_chart(
        plots,
        dates,
        arm_left,
        "arm",
        "Arm Development",
        "law & justice",
        "Arm Left in cm",
        arm_right,
        "Arm Right in cm",
    )

    generate_line_chart(
        plots,
        dates,
        chest,
        "chest",
        "Chest Development",
        "pride factor",
        "Chest in cm",
    )

    return plots


# =============================================================================
# Meal Plan Functions
# =============================================================================


def get_meals():
    meals = Meal.objects.all().prefetch_related("ingredients")

    meal_dict = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "snack": [],
    }

    for meal in meals:
        meal_data = {
            "name": meal.name,
            "category": meal.category,
            "ingredients": [],
        }

        for ingredient in meal.ingredients.all():
            ingredient_data = {
                "name": ingredient.name,
                "amount": ingredient.amount,
                "unit": ingredient.unit,
            }

            meal_data["ingredients"].append(ingredient_data)

        meal_dict[meal.category].append(meal_data)

    return meal_dict


# =============================================================================
# Training History Functions
# =============================================================================


def get_training_history():
    training_history_entries = (
        TrainingHistory.objects.all()
        .prefetch_related("exercises")
        .order_by("-date")
    )

    training_history = {}

    for training_history_entry in training_history_entries:
        month_key = training_history_entry.date.strftime("%B %Y")

        if month_key not in training_history:
            training_history[month_key] = []

        training_history_data = {
            "date": training_history_entry.date,
            "training_type": training_history_entry.training_type,
            "training_program": training_history_entry.training_program,
            "training_note": training_history_entry.training_note,
            "exercises": [],
        }

        for exercise in training_history_entry.exercises.all():
            exercise_data = {
                "name": exercise.name,
                "sets_reps": exercise.sets_reps,
                "weight": exercise.weight,
                "equipment": exercise.get_equipment_display(),
                "duration": exercise.duration,
                "distance": exercise.distance,
                "kcal": exercise.kcal,
            }

            training_history_data["exercises"].append(exercise_data)

        training_history[month_key].append(training_history_data)

    return training_history




# =============================================================================
# Exercise Plan Functions
# =============================================================================

def get_exercises():
    exercises = (
        Exercise.objects
        .values(
            "exercise_name",
            "exercise_musclegroup",
            "exercise_equipment",
        )
        .order_by(
            "exercise_musclegroup",
            "exercise_name",
            "exercise_equipment",
        )
    )

    exercises_by_musclegroup = defaultdict(list)

    for exercise in exercises:
        exercises_by_musclegroup[exercise["exercise_musclegroup"]].append(
            {
                "exercise_name": exercise["exercise_name"],
                "exercise_musclegroup": exercise["exercise_musclegroup"],
                "exercise_equipment": exercise["exercise_equipment"],
            }
        )

    return dict(exercises_by_musclegroup)

# =============================================================================
# Training Plan Functions
# =============================================================================


def get_training_planner():
    training_plans = (
        TrainingPlan.objects.all()
        .prefetch_related("exercises")
        .order_by("-date")
    )

    training_planner = {}

    for training_plan in training_plans:
        month_key = training_plan.date.strftime("%B %Y")

        if month_key not in training_planner:
            training_planner[month_key] = []

        training_plan_data = {
            "date": training_plan.date,
            "training_type": training_plan.training_type,
            "training_program": training_plan.training_program,
            "training_note": training_plan.training_note,
            "exercises": [],
        }

        for exercise in training_plan.exercises.all():
            exercise_data = {
                "name": exercise.name,
                "sets_reps": exercise.sets_reps,
                "weight": exercise.weight,
                "equipment": exercise.get_equipment_display(),
                "duration": exercise.duration,
            }

            training_plan_data["exercises"].append(exercise_data)

        training_planner[month_key].append(training_plan_data)

    return training_planner


# =============================================================================
# Context Helper Functions
# =============================================================================


def get_dashboard_context(request):
    return {
        "user_data": get_user_data(request),
        "current_salute": get_current_salute(),
        "current_date": get_current_date(),
        "current_nutrition": get_current_nutrition_data(),
        "exercise_types_as_donut_chart": get_exercise_types_as_donut_chart(),
        "weekly_split": get_current_weekly_split(),
        "daily_meal_suggestions": get_daily_meal_suggestions(),
        "days_trained": get_days_trained_data(),
        "average_training_days_per_week": get_average_training_days_per_week_data(),
        "body_measure_improvement": get_body_measure_improvement_data(),
        "youtube_channels": get_youtube_channels(),
    }


def get_body_measurements_context():
    return {
        "plots": get_body_measure_plots(),
        "body_measure_improvement": get_body_measure_improvement_data(),
    }


def get_meal_plan_context():
    return {
        "meals": get_meals(),
    }


def get_training_planner_context():
    return {
        "training_planner": get_training_planner(),
    }


def get_training_history_context():
    return {
        "training_history": get_training_history(),
    }

def get_exercises_context():
    return {
        "exercises_by_musclegroup": get_exercises(),
    }


def get_full_report_context(request):
    context = {}

    context.update(get_dashboard_context(request))
    context.update(get_body_measurements_context())
    context.update(get_training_planner_context())
    context.update(get_training_history_context())
    context.update(get_meal_plan_context())

    return context


# =============================================================================
# Views
# =============================================================================


def dashboard(request):
    return render(
        request,
        "tracker/dashboard.html",
        get_dashboard_context(request),
    )


def bodyMeasures(request):
    return render(
        request,
        "tracker/body_measures.html",
        get_body_measurements_context(),
    )


def mealPlan(request):
    return render(
        request,
        "tracker/meal_plan.html",
        get_meal_plan_context(),
    )


def trainingPlan(request):
    return render(
        request,
        "tracker/training_plan.html",
        get_training_planner_context(),
    )


def trainingHistory(request):
    return render(
        request,
        "tracker/training_history.html",
        get_training_history_context(),
    )


def exercises(request):
    return render(
        request,
        "tracker/exercises.html",
        get_exercises_context(),
    )

def credits(request):
    return render(request, "tracker/credits.html")


def export(request):
    return render(request, "tracker/export.html")


# =============================================================================
# PDF Export Views
# =============================================================================


def export_dashboard_pdf(request):
    return render_pdf(
        request,
        "tracker/reports/dashboard_report.html",
        get_dashboard_context(request),
        "dashboard_report.pdf",
    )


def export_body_measurements_pdf(request):
    return render_pdf(
        request,
        "tracker/reports/body_measurements_report.html",
        get_body_measurements_context(),
        "body_measurements_report.pdf",
    )


def export_training_plan_pdf(request):
    return render_pdf(
        request,
        "tracker/reports/training_plan_report.html",
        get_training_planner_context(),
        "training_plan_report.pdf",
    )


def export_training_history_pdf(request):
    return render_pdf(
        request,
        "tracker/reports/training_history_report.html",
        get_training_history_context(),
        "training_history_report.pdf",
    )


def export_meal_plan_pdf(request):
    return render_pdf(
        request,
        "tracker/reports/meal_plan_report.html",
        get_meal_plan_context(),
        "meal_plan_report.pdf",
    )


def export_all_pdf(request):
    return render_pdf(
        request,
        "tracker/reports/full_report.html",
        get_full_report_context(request),
        "fitness_report.pdf",
    )
