FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY pyproject.toml README.md requirements-runtime.lock requirements-build.lock ./
COPY src ./src
COPY bootstrap ./bootstrap
COPY server.py worker.py manage.py ./
# Install and verify from hash locks, then remove installer/bootstrap copies from
# the immutable runtime image (including their unused vendored dependencies).
RUN python -m pip install --require-hashes -r requirements-build.lock \
    && python -m pip install --require-hashes -r requirements-runtime.lock \
    && python -m pip install --no-deps --no-build-isolation . \
    && python -m pip check \
    && python -m pip uninstall --yes pip \
    && python -c "import importlib.util, pathlib, shutil, sysconfig; shutil.rmtree(pathlib.Path(sysconfig.get_path('stdlib')) / 'ensurepip'); assert importlib.util.find_spec('pip') is None; assert importlib.util.find_spec('ensurepip') is None"

USER app
EXPOSE 8000
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
