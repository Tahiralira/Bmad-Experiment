from unittest.mock import MagicMock, patch

from app.backend_pre_start import init, logger


def test_init_successful_connection() -> None:
    # WS9: this test was doubly fake — it patched "sqlmodel.Session" (the
    # module does `from sqlmodel import Session`, so the patch never
    # intercepted) and "asserted" via the misspelled non-assertion
    # `.called_once_with(...)` (always truthy; Python 3.13's mock rejects it).
    engine_mock = MagicMock()
    session_mock = MagicMock()
    # `with Session(engine) as session:` binds __enter__'s return value.
    session_mock.__enter__.return_value = session_mock

    with (
        patch("app.backend_pre_start.Session", return_value=session_mock),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        init(engine_mock)

    session_mock.exec.assert_called_once()
