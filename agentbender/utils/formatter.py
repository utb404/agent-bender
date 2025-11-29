"""Code formatter utilities."""

import subprocess
import tempfile
from pathlib import Path
from typing import Literal, Optional
import logging


logger = logging.getLogger(__name__)


class CodeFormatter:
    """Форматтер кода."""
    
    def __init__(
        self,
        style: Literal["black", "autopep8", "none"] = "black",
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация форматтера.
        
        Args:
            style: Стиль форматирования ("black", "autopep8", "none").
            logger: Логгер для записи операций.
        """
        self.style = style
        self.logger = logger or logging.getLogger(__name__)
    
    def format(self, code: str) -> str:
        """
        Форматирование кода.
        
        Args:
            code: Исходный код.
        
        Returns:
            str: Отформатированный код.
        """
        if self.style == "none":
            return code
        
        try:
            if self.style == "black":
                return self._format_with_black(code)
            elif self.style == "autopep8":
                return self._format_with_autopep8(code)
            else:
                return code
        except Exception as e:
            self.logger.warning(f"Ошибка при форматировании кода: {e}")
            return code
    
    def format_file(self, file_path: Path) -> None:
        """
        Форматирование файла.
        
        Args:
            file_path: Путь к файлу для форматирования.
        """
        if self.style == "none":
            return
        
        try:
            if self.style == "black":
                subprocess.run(
                    ["black", str(file_path)],
                    check=True,
                    capture_output=True
                )
            elif self.style == "autopep8":
                subprocess.run(
                    ["autopep8", "--in-place", str(file_path)],
                    check=True,
                    capture_output=True
                )
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Ошибка при форматировании файла {file_path}: {e}")
        except FileNotFoundError:
            self.logger.warning(f"Форматтер {self.style} не найден. Установите его для форматирования кода.")
    
    def _format_with_black(self, code: str) -> str:
        """Форматирование с помощью black."""
        try:
            result = subprocess.run(
                ["black", "--code", code],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: использование black через Python API
            try:
                import black
                mode = black.Mode()
                return black.format_str(code, mode=mode)
            except ImportError:
                self.logger.warning("Black не установлен. Код не будет отформатирован.")
                return code
    
    def _format_with_autopep8(self, code: str) -> str:
        """Форматирование с помощью autopep8."""
        try:
            import autopep8
            return autopep8.fix_code(code)
        except ImportError:
            self.logger.warning("Autopep8 не установлен. Код не будет отформатирован.")
            return code

