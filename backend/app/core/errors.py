class NeuroScanError(Exception):
    """Base exception for NeuroScan AI platform."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MriValidationError(NeuroScanError):
    """Raised when an uploaded MRI file fails dimension, orientation, or format checks."""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class ModelNotLoadedError(NeuroScanError):
    """Raised when segmentation is attempted but no trained model checkpoint exists."""
    def __init__(self, message: str = "Trained model checkpoint is unavailable. Please run training or provide a checkpoint."):
        super().__init__(message, status_code=503)


class InferenceError(NeuroScanError):
    """Raised when failure occurs during preprocessing or model forward-pass."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class FileTooLargeError(NeuroScanError):
    """Raised when an uploaded scan exceeds memory decompression or file size limits."""
    def __init__(self, message: str = "Uploaded file exceeds the maximum allowed size limit."):
        super().__init__(message, status_code=413)


class UnsupportedFormatError(NeuroScanError):
    """Raised when uploaded file has an unsupported extension or MIME type."""
    def __init__(self, message: str):
        super().__init__(message, status_code=415)
