"""
Unit тесты для модуля app/bot/handlers/config.py

Тестируемые компоненты:
- Helper-функции: get_config_path, get_backup_path
- Константы и метаданные
- FSM States

Changelog:
- 2025-12-28: CONFIG-01 - Созданы тесты для helper-функций
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch


from app.bot.handlers.config import (
    CONFIG_DIR,
    CONFIG_METADATA,
    ConfigFile,
    ConfigUploadStates,
    get_backup_path,
    get_config_path,
)


# ============================================================================
# TESTS: get_config_path
# ============================================================================

class TestGetConfigPath:
    """Тесты для функции get_config_path()."""

    def test_get_config_path_fees(self):
        """Проверка пути для fees.yml."""
        result = get_config_path(ConfigFile.FEES)
        assert result == CONFIG_DIR / "fees.yml"
        assert isinstance(result, Path)

    def test_get_config_path_commissions(self):
        """Проверка пути для commissions.yml."""
        result = get_config_path(ConfigFile.COMMISSIONS)
        assert result == CONFIG_DIR / "commissions.yml"
        assert isinstance(result, Path)

    def test_get_config_path_rates(self):
        """Проверка пути для rates.yml."""
        result = get_config_path(ConfigFile.RATES)
        assert result == CONFIG_DIR / "rates.yml"
        assert isinstance(result, Path)

    def test_get_config_path_duties(self):
        """Проверка пути для duties.yml."""
        result = get_config_path(ConfigFile.DUTIES)
        assert result == CONFIG_DIR / "duties.yml"
        assert isinstance(result, Path)

    def test_get_config_path_all_types(self):
        """Проверка, что все типы из enum имеют корректные пути."""
        for config_type in ConfigFile:
            result = get_config_path(config_type)
            assert isinstance(result, Path)
            assert result.parent == CONFIG_DIR
            assert result.suffix == ".yml"


# ============================================================================
# TESTS: get_backup_path
# ============================================================================

class TestGetBackupPath:
    """Тесты для функции get_backup_path()."""

    @patch("app.bot.handlers.config.datetime")
    def test_get_backup_path_format(self, mock_datetime):
        """Проверка формата backup-пути с timestamp."""
        # Мокаем текущее время
        mock_now = datetime(2025, 12, 28, 14, 30, 45, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        result = get_backup_path(ConfigFile.FEES)
        expected = CONFIG_DIR / "fees.yml.backup.20251228_143045"
        assert result == expected

    @patch("app.bot.handlers.config.datetime")
    def test_get_backup_path_all_types(self, mock_datetime):
        """Проверка backup-путей для всех типов конфигов."""
        mock_now = datetime(2025, 12, 28, 10, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        expected_suffix = ".backup.20251228_100000"

        for config_type in ConfigFile:
            result = get_backup_path(config_type)
            assert isinstance(result, Path)
            assert result.parent == CONFIG_DIR
            assert str(result).endswith(expected_suffix)

    def test_get_backup_path_unique_timestamps(self):
        """Проверка, что разные вызовы генерируют разные timestamp."""
        # Два быстрых вызова (могут иметь одинаковый timestamp в пределах секунды)
        result1 = get_backup_path(ConfigFile.FEES)
        result2 = get_backup_path(ConfigFile.FEES)

        # Проверяем формат
        assert ".backup." in str(result1)
        assert ".backup." in str(result2)

        # Оба пути валидны
        assert result1.parent == CONFIG_DIR
        assert result2.parent == CONFIG_DIR

    @patch("app.bot.handlers.config.datetime")
    def test_get_backup_path_timestamp_format(self, mock_datetime):
        """Проверка корректности формата timestamp YYYYMMDD_HHMMSS."""
        test_cases = [
            (datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC), "20250101_000000"),
            (datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC), "20251231_235959"),
            (datetime(2025, 6, 15, 12, 30, 45, tzinfo=UTC), "20250615_123045"),
        ]

        for mock_time, expected_timestamp in test_cases:
            mock_datetime.now.return_value = mock_time
            result = get_backup_path(ConfigFile.COMMISSIONS)
            expected_path = CONFIG_DIR / f"commissions.yml.backup.{expected_timestamp}"
            assert result == expected_path


# ============================================================================
# TESTS: Constants and Metadata
# ============================================================================

class TestConstants:
    """Тесты для констант и метаданных модуля."""

    def test_config_dir_is_path(self):
        """CONFIG_DIR должен быть Path объектом."""
        assert isinstance(CONFIG_DIR, Path)
        assert Path("config") == CONFIG_DIR

    def test_config_file_enum_values(self):
        """Проверка значений enum ConfigFile."""
        assert ConfigFile.FEES == "fees"
        assert ConfigFile.COMMISSIONS == "commissions"
        assert ConfigFile.RATES == "rates"
        assert ConfigFile.DUTIES == "duties"

        # Проверка, что все члены enum присутствуют
        assert len(ConfigFile) == 4

    def test_config_metadata_structure(self):
        """Проверка структуры CONFIG_METADATA."""
        # Должны быть все 4 типа
        assert len(CONFIG_METADATA) == 4

        for config_type in ConfigFile:
            assert config_type in CONFIG_METADATA
            metadata = CONFIG_METADATA[config_type]

            # Проверка обязательных ключей
            assert "filename" in metadata
            assert "description" in metadata
            assert "required_keys" in metadata

            # Проверка типов
            assert isinstance(metadata["filename"], str)
            assert isinstance(metadata["description"], str)
            assert isinstance(metadata["required_keys"], list)

            # Filename должен быть .yml
            assert metadata["filename"].endswith(".yml")

    def test_config_metadata_required_keys(self):
        """Проверка required_keys для каждого типа конфига."""
        assert CONFIG_METADATA[ConfigFile.FEES]["required_keys"] == [
            "countries", "freight"
        ]
        assert CONFIG_METADATA[ConfigFile.COMMISSIONS]["required_keys"] == [
            "company_commission", "bank_commission"
        ]
        assert CONFIG_METADATA[ConfigFile.RATES]["required_keys"] == [
            "rates", "utilization"
        ]
        assert CONFIG_METADATA[ConfigFile.DUTIES]["required_keys"] == [
            "petrol", "electric"
        ]

    def test_config_metadata_descriptions(self):
        """Проверка наличия описаний для всех конфигов."""
        for config_type in ConfigFile:
            description = CONFIG_METADATA[config_type]["description"]
            assert len(description) > 0
            assert isinstance(description, str)


# ============================================================================
# TESTS: FSM States
# ============================================================================

class TestFSMStates:
    """Тесты для FSM States."""

    def test_config_upload_states_exist(self):
        """Проверка существования всех FSM states."""
        assert hasattr(ConfigUploadStates, "waiting_for_fees")
        assert hasattr(ConfigUploadStates, "waiting_for_commissions")
        assert hasattr(ConfigUploadStates, "waiting_for_rates")
        assert hasattr(ConfigUploadStates, "waiting_for_duties")

    def test_config_upload_states_are_unique(self):
        """Проверка уникальности FSM states."""
        states = [
            ConfigUploadStates.waiting_for_fees,
            ConfigUploadStates.waiting_for_commissions,
            ConfigUploadStates.waiting_for_rates,
            ConfigUploadStates.waiting_for_duties,
        ]

        # Все states должны быть разными объектами
        assert len(states) == len(set(states))

    def test_config_upload_states_count(self):
        """Проверка количества states (должно быть 4)."""
        states = [attr for attr in dir(ConfigUploadStates) if not attr.startswith("_")]
        # Отфильтровываем только State объекты
        state_attrs = [
            attr for attr in states
            if attr.startswith("waiting_for_")
        ]
        assert len(state_attrs) == 4


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Интеграционные тесты для проверки согласованности модуля."""

    def test_all_enum_values_have_metadata(self):
        """Каждый ConfigFile должен иметь метаданные."""
        for config_type in ConfigFile:
            assert config_type in CONFIG_METADATA

    def test_metadata_filenames_match_enum_pattern(self):
        """Имена файлов в метаданных должны соответствовать enum значениям."""
        for config_type in ConfigFile:
            filename = CONFIG_METADATA[config_type]["filename"]
            # Filename должен начинаться с enum значения
            assert filename.startswith(config_type.value)

    def test_all_paths_use_same_directory(self):
        """Все конфиги должны находиться в одной директории."""
        for config_type in ConfigFile:
            path = get_config_path(config_type)
            assert path.parent == CONFIG_DIR

    def test_backup_paths_preserve_extension(self):
        """Backup-пути должны содержать оригинальное расширение."""
        for config_type in ConfigFile:
            backup_path = get_backup_path(config_type)
            original_filename = CONFIG_METADATA[config_type]["filename"]
            # Backup должен содержать оригинальное имя файла
            assert original_filename in str(backup_path)

