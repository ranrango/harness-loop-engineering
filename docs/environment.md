# Environment

This project uses Python 3.9 or newer and the Ultralytics YOLOv8 stack.

## Python Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Core Dependencies

Declared in `pyproject.toml`:

| package | version |
| --- | --- |
| ultralytics | >= 8.2.0 |
| opencv-python | >= 4.8.0 |
| numpy | >= 1.24.0 |
| matplotlib | >= 3.7.0 |
| torch | >= 2.0.0 |
| torchvision | >= 0.15.0 |

Development tools:

| package | purpose |
| --- | --- |
| jupyter | notebooks and analysis |
| black | formatting |
| pytest | tests |

Optional smoke-test dependency:

```bash
python -m pip install -e ".[smoke]"
```

This is only needed if you want to run `test.py`.

## Smoke Test Credential

`test.py` reads the DeepSeek API key from the local shell environment:

```bash
export DEEPSEEK_API_KEY="your_local_key"
python test.py
```

Do not commit real API keys, `.env` files, key files, logs, or screenshots that expose credentials.

## Suggested Verification

```bash
python -c "import ultralytics, torch; print(ultralytics.__version__); print(torch.__version__)"
python -m py_compile test.py src/detect.py scripts/convert_visdrone_to_yolo.py
```

Use CPU by default unless a GPU-specific environment has been configured and tested.
