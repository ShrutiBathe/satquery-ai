
from geo.validation import validate_images
from geo.preprocessing import preprocess_images


def test_vqa_validation():
    result = validate_images(
        ["test_satellite.tif"],
        "vqa"
    )
    assert result["valid"] is True


def test_change_detection_validation():
    result = validate_images(
        [
            "test_satellite.tif",
            "test_satellite_different_grid.tif"
        ],
        "change_detection"
    )
    assert result["valid"] is True


def test_optical_sar_validation():
    result = validate_images(
        [
            "test_satellite.tif",
            "test_satellite_different_grid.tif"
        ],
        "optical_sar"
    )
    assert result["valid"] is True


def test_vqa_preprocessing():
    result = preprocess_images(
        ["test_satellite.tif"],
        "vqa"
    )
    assert result["success"] is True
    assert len(result["image_paths"]) == 1


def test_change_detection_preprocessing():
    result = preprocess_images(
        [
            "test_satellite.tif",
            "test_satellite_different_grid.tif"
        ],
        "change_detection"
    )
    assert result["success"] is True
    assert result["metadata"]["aligned"] is True
    assert len(result["image_paths"]) == 2


def test_optical_sar_preprocessing():
    result = preprocess_images(
        [
            "test_satellite.tif",
            "test_satellite_different_grid.tif"
        ],
        "optical_sar"
    )
    assert result["success"] is True
    assert result["metadata"]["paired"] is True
    assert len(result["image_paths"]) == 2
