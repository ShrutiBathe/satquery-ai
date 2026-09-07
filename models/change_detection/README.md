# SatQuery AI - Change Detection

This module provides bi-temporal satellite image change detection
using ChangeFormerV6.

## Public API

The module exposes one main function:

```python
from models.change_detection import run_change_detection

result = run_change_detection(
    before_path,
    after_path,
)