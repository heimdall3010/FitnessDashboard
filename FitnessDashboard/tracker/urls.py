from django.urls import path
from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("body-measures/", views.bodyMeasures, name="body_measures"),
    path("meal-plan/", views.mealPlan, name="meal_plan"),
    path("training-plan/", views.trainingPlan, name="training_plan"),
    path("training-history/", views.trainingHistory, name="training_history"),
    path("exercises/", views.exercises, name="exercises"),
    path("credits/", views.credits, name="credits"),

    path("export/", views.export, name="export"),
    path("export/dashboard/pdf/", views.export_dashboard_pdf, name="export_dashboard_pdf"),
    path("export/body-measurements/pdf/", views.export_body_measurements_pdf, name="export_body_measurements_pdf"),
    path("export/training-plan/pdf/", views.export_training_plan_pdf, name="export_training_plan_pdf"),
    path("export/training-history/pdf/", views.export_training_history_pdf, name="export_training_history_pdf"),
    path("export/meal-plan/pdf/", views.export_meal_plan_pdf, name="export_meal_plan_pdf"),
    path("export/all/pdf/", views.export_all_pdf, name="export_all_pdf"),
]
