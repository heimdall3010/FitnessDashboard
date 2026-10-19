from django.db import models


class YoutubeChannel(models.Model):
    youtube_channel_name = models.CharField(max_length=100, null=True, blank=True)
    youtube_channel_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"YoutubeChannel {self.youtube_channel_name}"


class Exercise(models.Model):
    exercise_name = models.CharField(max_length=100, null=True, blank=True)
    exercise_musclegroup = models.CharField(max_length=100, null=True, blank=True)
    exercise_equipment = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Exercise {self.exercise_name}"


class BodyMeasure(models.Model):
    date = models.DateField()
    weight = models.FloatField(null=True, blank=True)
    waist = models.FloatField(null=True, blank=True)
    chest = models.FloatField(null=True, blank=True)
    arm_left = models.FloatField(null=True, blank=True)
    arm_right = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"BodyMeasure {self.date}"


from django.db import models, transaction


class TrainingHistory(models.Model):
    STRENGTH = "Strength"
    CARDIO = "Cardio"
    YOGA_STRETCHING = "Yoga & Stretching"

    TRAINING_TYPE_CHOICES = [
        (STRENGTH, "Strength"),
        (CARDIO, "Cardio"),
        (YOGA_STRETCHING, "Yoga & Stretching"),
    ]

    date = models.DateField()

    source_training_plan = models.ForeignKey(
        "TrainingPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="training_history_entries",
    )

    training_type = models.CharField(
        max_length=100,
        choices=TRAINING_TYPE_CHOICES,
        default=STRENGTH,
    )

    training_program = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    training_note = models.TextField(
        null=True,
        blank=True,
    )

    def apply_source_training_plan(self) -> None:
        """
        Copies the general data from the selected training plan.

        The date and source_training_plan fields are preserved.
        """
        if self.source_training_plan is None:
            return

        self.training_type = self.source_training_plan.training_type
        self.training_program = self.source_training_plan.training_program
        self.training_note = self.source_training_plan.training_note

    @transaction.atomic
    def replace_exercises_from_training_plan(self) -> None:
        """
        Deletes all existing history exercises and replaces them
        with exercises from the selected training plan.
        """
        if self.source_training_plan is None:
            return

        self.exercises.all().delete()

        history_exercises = [
            TrainingHistoryExerciseEntry(
                training_history=self,
                name=plan_exercise.name,
                sets_reps=plan_exercise.sets_reps,
                weight=plan_exercise.weight,
                equipment=plan_exercise.equipment,
                duration=plan_exercise.duration,
            )
            for plan_exercise in self.source_training_plan.exercises.all()
        ]

        TrainingHistoryExerciseEntry.objects.bulk_create(
            history_exercises
        )

    def __str__(self):
        return f"TrainingHistory {self.date}"


class TrainingPlan(models.Model):
    STRENGTH = "Strength"
    CARDIO = "Cardio"
    YOGA_STRETCHING = "Yoga & Stretching"

    TRAINING_TYPE_CHOICES = [
        (STRENGTH, "Strength"),
        (CARDIO, "Cardio"),
        (YOGA_STRETCHING, "Yoga & Stretching"),
    ]

    date = models.DateField()

    training_type = models.CharField(
        max_length=100,
        choices=TRAINING_TYPE_CHOICES,
        default=STRENGTH,
    )

    training_program = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    training_note = models.TextField(
        null=True,
        blank=True,
    )

    def __str__(self):
        program = self.training_program or self.training_type
        return f"{self.date} | {program}"


class ExerciseBase(models.Model):
    DB = "dumbbell"
    DBS = "2 dumbbells"
    RB = "resistance bands"
    FW = "foot weight"
    BENCH = "bench"
    BIKE = "bike"
    BW = "body weight"
    YM = "yoga matt"
    PL = "plate(s)"

    EQUIPMENT_CHOICES = [
        (DB, "dumbbell"),
        (DBS, "2 dumbbells"),
        (RB, "resistance bands"),
        (FW, "foot weight"),
        (BENCH, "bench"),
        (BIKE, "bike"),
        (BW, "body weight"),
        (YM, "yoga matt"),
        (PL, "plate(s)"),
    ]

    name = models.CharField(max_length=200)
    sets_reps = models.CharField(max_length=50, null=True, blank=True)
    weight = models.CharField(max_length=50, null=True, blank=True)

    equipment = models.CharField(
        max_length=50,
        choices=EQUIPMENT_CHOICES,
        default=DB,
    )

    duration = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        abstract = True


class TrainingHistoryExerciseEntry(ExerciseBase):
    training_history = models.ForeignKey(
        TrainingHistory,
        on_delete=models.CASCADE,
        related_name="exercises",
    )

    distance = models.CharField(max_length=50, null=True, blank=True)
    kcal = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} | {self.training_history}"


class TrainingPlanExerciseEntry(ExerciseBase):
    training_plan = models.ForeignKey(
        TrainingPlan,
        on_delete=models.CASCADE,
        related_name="exercises",
    )

    def __str__(self):
        return f"{self.name} | {self.training_plan}"


class Meal(models.Model):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

    CATEGORY_CHOICES = [
        (BREAKFAST, "Breakfast"),
        (LUNCH, "Lunch"),
        (DINNER, "Dinner"),
        (SNACK, "Snack"),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default=BREAKFAST,
    )

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Ingredient(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="ingredients")

    name = models.CharField(max_length=200)
    amount = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.meal.name})"


class Nutrition(models.Model):
    date = models.DateField()

    water_l = models.FloatField(null=True, blank=True)
    water_l_aim = models.FloatField(null=True, blank=True, default=3.0)

    protein_g = models.FloatField(null=True, blank=True)
    protein_g_aim = models.FloatField(null=True, blank=True, default=150.0)

    calories_kcal = models.FloatField(null=True, blank=True)
    calories_kcal_aim = models.FloatField(null=True, blank=True, default=2500.0)

    sleep_h = models.FloatField(null=True, blank=True)
    sleep_h_aim = models.FloatField(null=True, blank=True, default=8.0)

    def __str__(self):
        return f"Nutrition: {self.date}"
