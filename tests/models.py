from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from enum import Enum

class DataSourceType(Enum):
    DB = "DB"
    BIGQUERY = "BigQuery"

class OperatorType(Enum):
    APPROX_EQUAL = "Approximately equal"
    CHANGE_WITHIN_RANGE = "Change within range"
    EQUAL = "=="
    GREATER_EQUAL = ">="
    GREATER_THAN = ">"
    LESS_EQUAL = "<="
    LESS_THAN = "<"

class ScheduleType(Enum):
    DAILY = "Daily"
    HOURLY = "Hourly"

class TestData(models.Model):
    data_source_type = models.CharField(
        max_length=10,
        choices=[(tag.name, tag.value) for tag in DataSourceType]
    )
    query = models.TextField(help_text="SQL query (must return a single scalar value)")

    def __str__(self):
        return f"{self.data_source_type}: {self.query[:50]}..."

class TestCase(models.Model):
    data_a = models.ForeignKey(TestData, on_delete=models.CASCADE, related_name="data_a_cases")
    data_b = models.ForeignKey(TestData, null=True, blank=True, on_delete=models.CASCADE, related_name="data_b_cases")
    constant_b = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tolerance = models.DecimalField(default=1.0, max_digits=5, decimal_places=2)
    operator = models.CharField(
        max_length=30,
        choices=[(op.name, op.value) for op in OperatorType]
    )

    def validate_test_case(self):
        if not self.data_b and self.constant_b is None:
            raise ValueError("Either data_b or constant_b must be provided.")

    def __str__(self):
        return f"TestCase ({self.operator})"

class TestSuite(models.Model):
    name = models.CharField(max_length=100)
    test_cases = models.ManyToManyField(TestCase, through="TestSuiteCase")
    query_parameters = models.JSONField(null=True, blank=True)
    bq_service_account_credentials = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class TestSuiteCase(models.Model):
    test_suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE)
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)

class ScheduledTest(models.Model):
    test_suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE)
    frequency = models.CharField(max_length=10, choices=[(freq.name, freq.value) for freq in ScheduleType])
    utc_hour = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="UTC hour for execution (ignored for hourly tests)"
    )

    def __str__(self):
        return f"Scheduled {self.test_suite.name} ({self.frequency} at {self.utc_hour}h)"

class TestSubscriber(models.Model):
    webhook_url = models.URLField()

    def __str__(self):
        return self.webhook_url

class TestCaseSubscription(models.Model):
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(TestSubscriber, on_delete=models.CASCADE)

class TestSuiteSubscription(models.Model):
    test_suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(TestSubscriber, on_delete=models.CASCADE)
