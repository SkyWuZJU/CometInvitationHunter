"""Mock resend module for testing."""

class MockEmails:
    @staticmethod
    def send(data):
        class MockResponse:
            def __init__(self):
                self.id = 'test-email-id'
        return MockResponse()

class MockResend:
    api_key = None
    Emails = MockEmails()

# Create module-level attributes
api_key = None
Emails = MockEmails()