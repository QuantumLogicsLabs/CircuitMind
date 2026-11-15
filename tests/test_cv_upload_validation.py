"""Upload validation for the CV module.

The API previously accepted any ``image/*`` upload with no size cap and passed
the client filename's extension straight to a temp file. These tests cover the
pure validation helper, which runs without OpenCV/Ultralytics installed.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cv_module.upload_validation import (
    ALLOWED_CONTENT_TYPES,
    MAX_UPLOAD_BYTES,
    UploadValidationError,
    validate_upload,
)


@pytest.mark.parametrize(
    "content_type,filename,expected",
    [
        ("image/png", "schematic.png", ".png"),
        ("image/jpeg", "schematic.jpg", ".jpg"),
    ],
)
def test_supported_content_types_are_accepted(content_type, filename, expected):
    assert validate_upload(content_type, filename, 1024) == expected


@pytest.mark.parametrize("content_type", ["image/svg+xml", "image/tiff", "text/plain", None, ""])
def test_unsupported_content_types_are_rejected(content_type):
    with pytest.raises(UploadValidationError):
        validate_upload(content_type, "schematic.png", 1024)


@pytest.mark.parametrize("filename", ["schematic.gif", "schematic.bmp", "schematic.webp.pdf"])
def test_unsupported_extensions_are_rejected(filename):
    with pytest.raises(UploadValidationError):
        validate_upload("image/png", filename, 1024)


def test_uppercase_extension_is_accepted_and_normalized():
    assert validate_upload("image/png", "SCHEMATIC.PNG", 10) == ".png"


def test_jpeg_extension_is_normalized_to_jpg():
    assert validate_upload("image/jpeg", "photo.jpeg", 10) == ".jpg"


def test_missing_filename_falls_back_to_content_type_suffix():
    assert validate_upload("image/png", None, 10) == ".png"
    assert validate_upload("image/jpeg", "", 10) == ".jpg"


def test_empty_upload_is_rejected():
    with pytest.raises(UploadValidationError, match="empty"):
        validate_upload("image/png", "schematic.png", 0)


def test_oversized_upload_is_rejected():
    with pytest.raises(UploadValidationError, match="too large"):
        validate_upload("image/png", "schematic.png", MAX_UPLOAD_BYTES + 1)


def test_upload_at_limit_is_accepted():
    assert validate_upload("image/png", "schematic.png", MAX_UPLOAD_BYTES) == ".png"
