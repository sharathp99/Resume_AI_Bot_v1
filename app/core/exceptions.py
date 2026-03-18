class ApplicationError(Exception):
    """Base application error."""


class IngestionError(ApplicationError):
    """Raised when a file ingestion step fails."""


class ExtractionError(ApplicationError):
    """Raised when structured extraction fails."""


class SearchError(ApplicationError):
    """Raised when search or retrieval fails."""


class ExportError(ApplicationError):
    """Raised when export generation fails."""
