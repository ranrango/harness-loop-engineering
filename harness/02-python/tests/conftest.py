"""
conftest.py — 共享 fixture

放在这里的 fixture 对整个 tests/ 目录下的所有测试文件可见，
不需要显式 import。
"""

import pytest


@pytest.fixture(autouse=False)
def assert_no_side_effects(capsys):
    """
    可选 fixture：验证测试没有打印任何内容（副作用检查）。
    在测试上加 @pytest.mark.usefixtures("assert_no_side_effects") 来启用。
    """
    yield
    captured = capsys.readouterr()
    # 如果测试输出了内容，发出警告（不强制失败）
    if captured.out:
        import warnings
        warnings.warn(f"Test printed to stdout: {captured.out!r}")
