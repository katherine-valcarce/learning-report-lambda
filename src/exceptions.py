class LearningReportError(Exception):
    """Base exception for the learning report lambda."""


class ValidationError(LearningReportError):
    """Raised when the incoming event does not comply with the contract."""


class PdfGenerationError(LearningReportError):
    """Raised when the PDF generation process fails."""


class StorageError(LearningReportError):
    """Raised when upload to storage fails."""


class EmailDeliveryError(LearningReportError):
    """Raised when the email notification cannot be sent."""
