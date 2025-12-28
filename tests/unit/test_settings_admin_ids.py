"""
Тесты для AppSettings.admin_ids property.
"""

from unittest.mock import patch

from app.core.settings import AppSettings


def test_admin_ids_empty_string():
    """Тест: пустая строка возвращает пустое множество."""
    with patch.dict("os.environ", {"ADMIN_USER_IDS": ""}):
        settings = AppSettings()
        assert settings.admin_ids == set()


def test_admin_ids_single_id():
    """Тест: один ID."""
    with patch.dict("os.environ", {"ADMIN_USER_IDS": "123456"}):
        settings = AppSettings()
        assert settings.admin_ids == {123456}


def test_admin_ids_multiple_ids():
    """Тест: несколько IDs через запятую."""
    with patch.dict("os.environ", {"ADMIN_USER_IDS": "123456,789012,555666"}):
        settings = AppSettings()
        assert settings.admin_ids == {123456, 789012, 555666}


def test_admin_ids_with_spaces():
    """Тест: IDs с пробелами."""
    with patch.dict("os.environ", {"ADMIN_USER_IDS": "123456, 789012 , 555666"}):
        settings = AppSettings()
        assert settings.admin_ids == {123456, 789012, 555666}


def test_admin_ids_with_empty_elements():
    """Тест: пустые элементы между запятыми игнорируются."""
    with patch.dict("os.environ", {"ADMIN_USER_IDS": "123456,,789012,  ,555666"}):
        settings = AppSettings()
        assert settings.admin_ids == {123456, 789012, 555666}


def test_admin_ids_invalid_value():
    """Тест: невалидное значение возвращает пустое множество."""
    with patch.dict("os.environ", {"ADMIN_USER_IDS": "123456,abc,789012"}):
        settings = AppSettings()
        assert settings.admin_ids == set()


def test_admin_ids_duplicates():
    """Тест: дубликаты автоматически удаляются (set свойство)."""
    with patch.dict("os.environ", {"ADMIN_USER_IDS": "123456,123456,789012"}):
        settings = AppSettings()
        assert settings.admin_ids == {123456, 789012}
        assert len(settings.admin_ids) == 2
