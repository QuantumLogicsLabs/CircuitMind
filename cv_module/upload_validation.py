"""
CircuitMind - Computer Vision upload validation
cv_module/upload_validation.py

Pure validation for uploaded circuit images. Kept separate from cv_api so it
can be unit-tested without OpenCV / Ultralytics installed.
"""

from pathlib import Path

# Map accepted MIME types to the suffix used for the temporary file.
ALLOWED_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg"}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MiB


class UploadValidationError(ValueError):
    """Raised when an uploaded image fails validation."""


def validate_upload(content_type: str | None, filename: str | None, size: int) -> str:
    """Validate an uploaded image and return the temp-file suffix to use.

    ``content_type`` is the client-declared MIME type; it must be one of the
    supported image types (``image/*`` alone is too permissive — an SVG or
    TIFF cannot be decoded by the OpenCV pipeline). ``size`` is the number of
    bytes read.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UploadValidationError(
            "File must be a PNG or JPEG image (got "
            f"{content_type or 'no content type'})."
        )

    suffix = Path(filename or "").suffix.lower()
    if suffix and suffix not in ALLOWED_SUFFIXES:
        raise UploadValidationError(
            f"Unsupported file extension '{suffix}'. Use .png, .jpg or .jpeg."
        )

    if size <= 0:
        raise UploadValidationError("Uploaded image is empty.")

    if size > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise UploadValidationError(
            f"Image is too large ({size} bytes). Limit is {limit_mb} MiB."
        )

    if suffix == ".jpeg":
        return ".jpg"
    return suffix or ALLOWED_CONTENT_TYPES[content_type]
