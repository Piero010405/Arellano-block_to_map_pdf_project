class BlockPdfError(Exception):
    """Base exception for this project."""


class ConfigurationError(BlockPdfError):
    """Raised when configuration is invalid."""


class DatasetError(BlockPdfError):
    """Raised when the Excel dataset cannot be processed."""


class KmlError(BlockPdfError):
    """Raised when the KML file cannot be parsed."""


class MapProviderError(BlockPdfError):
    """Raised when the map provider returns an error."""
