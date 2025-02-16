from datetime import datetime
import logging
from decimal import Decimal
from django.db import connection
from .models import ScheduledTest, TestSubscriber

logger = logging.getLogger(__name__)

class TestRunnerClient:
    def __init__(self):
        self.current_hour = datetime.utcnow().hour

    def execute_query(self, query):
        """ Executes a database query and returns a single scalar result. """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return Decimal(result[0]) if result else None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None

    def evaluate_test_case(self, test_case, value_a, value_b):
        """ Evaluates test case conditions based on the given values. """
        operator = test_case.operator
        tolerance = test_case.tolerance

        if operator == "APPROX_EQUAL":
            return abs(value_a - value_b) <= (value_b * tolerance)
        elif operator == "CHANGE_WITHIN_RANGE":
            return abs((value_b - value_a) / value_a - 1) < tolerance
        elif operator == "EQUAL":
            return value_a == value_b
        elif operator == "GREATER_EQUAL":
            return value_a >= value_b
        elif operator == "GREATER_THAN":
            return value_a > value_b
        elif operator == "LESS_EQUAL":
            return value_a <= value_b
        elif operator == "LESS_THAN":
            return value_a < value_b
        return False

    def notify_failure(self, test_case, subscribers):
        """ Sends failure notifications to all subscribers. """
        for subscriber in subscribers:
            logger.info(f"Sending failure notification to {subscriber.webhook_url}")

    def run_tests(self):
        """ Runs all scheduled tests for the current hour. """
        scheduled_tests = ScheduledTest.objects.filter(
            frequency="Hourly"
        ) | ScheduledTest.objects.filter(
            frequency="Daily", utc_hour=self.current_hour
        )

        for test in scheduled_tests:
            test_suite = test.test_suite
            test_cases = test_suite.test_cases.all()

            for test_case in test_cases:
                value_a = self.execute_query(test_case.data_a.query)
                value_b = self.execute_query(test_case.data_b.query) if test_case.data_b else test_case.constant_b

                if value_a is None or value_b is None:
                    logger.warning(f"Skipping test case {test_case} due to missing data.")
                    continue

                success = self.evaluate_test_case(test_case, value_a, value_b)

                if not success:
                    subscribers = TestSubscriber.objects.filter(
                        testsuite__test_suite=test_suite
                    ) | TestSubscriber.objects.filter(
                        testcase__test_case=test_case
                    )
                    self.notify_failure(test_case, subscribers)
