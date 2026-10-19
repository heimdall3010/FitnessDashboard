from django.contrib import admin

from .models import BodyMeasure
from .models import TrainingHistory
from .models import TrainingPlan
from .models import TrainingHistoryExerciseEntry
from .models import TrainingPlanExerciseEntry
from .models import Meal
from .models import Ingredient
from .models import Nutrition
from .models import Exercise
from .models import YoutubeChannel


# =============================================================================
# YouTubeChannel
# =============================================================================

@admin.register(YoutubeChannel)
class YoutubeChannelAdmin(admin.ModelAdmin):
    list_display = (
        "youtube_channel_name",
        "youtube_channel_id",
    )

    list_filter = (
        "youtube_channel_name",
    )

    ordering = ("youtube_channel_name",)


# =============================================================================
# Exercise
# =============================================================================

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = (
        "exercise_name",
        "exercise_musclegroup",
        "exercise_equipment",

    )

    list_filter = (
        "exercise_musclegroup",
    )

    ordering = ("exercise_musclegroup",)

# =============================================================================
# Body Measures
# =============================================================================

@admin.register(BodyMeasure)
class BodyMeasureAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "weight",
        "waist",
        "chest",
        "arm_right",
        "arm_left",
    )

    list_filter = (
        "date",
    )

    date_hierarchy = "date"
    ordering = ("-date",)


# =============================================================================
# Training History
# =============================================================================

class TrainingHistoryExerciseEntryInline(admin.TabularInline):
    model = TrainingHistoryExerciseEntry
    extra = 0


@admin.register(TrainingHistory)
class TrainingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "training_type",
        "training_program",
        "training_note",
        "exercise_count",
    )

    fields = (
        "date",
        "source_training_plan",
        "training_type",
        "training_program",
        "training_note",
    )

    date_hierarchy = "date"
    ordering = ("-date",)

    inlines = [
        TrainingHistoryExerciseEntryInline,
    ]

    @admin.display(description="Exercises")
    def exercise_count(self, obj):
        return obj.exercises.count()

    def save_model(self, request, obj, form, change):
        if obj.source_training_plan is not None:
            obj.apply_source_training_plan()

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        training_history = form.instance

        if training_history.source_training_plan is not None:
            training_history.replace_exercises_from_training_plan()


# =============================================================================
# Training Plan
# =============================================================================

class TrainingPlanExerciseEntryInline(admin.TabularInline):
    model = TrainingPlanExerciseEntry
    extra = 0

    fields = (
        "name",
        "sets_reps",
        "weight",
        "duration",
        "equipment",
    )

    show_change_link = False


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "training_type",
        "training_program",
        "training_note",
        "exercise_count",
    )

    list_filter = (
        "training_type",
        "training_program",
        "date",
    )

    search_fields = (
        "training_type",
        "training_program",
        "exercises__name",
    )

    date_hierarchy = "date"
    ordering = ("-date",)

    inlines = [
        TrainingPlanExerciseEntryInline,
    ]

    @admin.display(description="Exercises")
    def exercise_count(self, obj):
        return obj.exercises.count()


# =============================================================================
# Meals
# =============================================================================

class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 0

    fields = (
        "name",
        "amount",
        "unit",
    )


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "ingredients_count",
    )

    list_filter = (
        "category",
    )

    search_fields = (
        "name",
        "category",
        "ingredients__name",
    )

    ordering = (
        "category",
        "name",
    )

    inlines = [
        IngredientInline,
    ]

    @admin.display(description="Ingredients")
    def ingredients_count(self, obj):
        return obj.ingredients.count()


# =============================================================================
# Nutrition
# =============================================================================

@admin.register(Nutrition)
class NutritionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "water_l",
        "water_l_aim",
        "protein_g",
        "protein_g_aim",
        "calories_kcal",
        "calories_kcal_aim",
        "sleep_h",
        "sleep_h_aim",
    )

    list_filter = (
        "date",
    )

    date_hierarchy = "date"
    ordering = ("-date",)
