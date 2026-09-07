
import numpy as np
import rasterio
from rasterio.transform import from_origin

from geo.preprocessing import preprocess_images, preprocess_optical_sar
from geo.validation import validate_images


def _write_raster(path, count=3, width=256, height=256, value=1):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=count,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_origin(0, 1, 1, 1),
    ) as dataset:
        dataset.write(np.full((count, height, width), value, dtype=np.uint8))


def test_vqa_validation(tmp_path):
    image = tmp_path / "image.tif"
    _write_raster(image)
    result = validate_images(
        [str(image)],
        "vqa"
    )
    assert result["valid"] is True


def test_change_detection_validation(tmp_path):
    before = tmp_path / "before.tif"
    after = tmp_path / "after.tif"
    _write_raster(before)
    _write_raster(after)
    result = validate_images(
        [str(before), str(after)],
        "change_detection"
    )
    assert result["valid"] is True


def test_optical_sar_validation(tmp_path):
    optical = tmp_path / "optical.tif"
    vv = tmp_path / "vv.tif"
    vh = tmp_path / "vh.tif"
    _write_raster(optical, count=3)
    _write_raster(vv, count=1)
    _write_raster(vh, count=1)
    result = validate_images(
        [str(optical), str(vv), str(vh)],
        "optical_sar"
    )
    assert result["valid"] is True


def test_vqa_preprocessing(tmp_path):
    image = tmp_path / "image.tif"
    _write_raster(image)
    result = preprocess_images(
        [str(image)],
        "vqa",
        output_dir=tmp_path / "processed",
    )
    assert result["success"] is True
    assert len(result["image_paths"]) == 1


def test_change_detection_preprocessing(tmp_path):
    before = tmp_path / "before.tif"
    after = tmp_path / "after.tif"
    _write_raster(before)
    _write_raster(after)
    result = preprocess_images(
        [str(before), str(after)],
        "change_detection",
        output_dir=tmp_path / "processed",
    )
    assert result["success"] is True
    assert result["metadata"]["aligned"] is True
    assert len(result["image_paths"]) == 2


def test_optical_sar_preprocessing(tmp_path):
    optical = tmp_path / "optical.tif"
    vv = tmp_path / "vv.tif"
    vh = tmp_path / "vh.tif"
    _write_raster(optical, count=3)
    _write_raster(vv, count=1)
    _write_raster(vh, count=1)
    result = preprocess_optical_sar(
        str(optical),
        str(vv),
        str(vh),
    )
    assert result["success"] is True
    assert result["metadata"]["paired"] is True
    assert len(result["image_paths"]) == 3
