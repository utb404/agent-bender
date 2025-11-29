"""File management utilities."""

from pathlib import Path
from typing import Dict, Optional
import logging


logger = logging.getLogger(__name__)


class FileManager:
    """Менеджер файлов для сохранения сгенерированного кода."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Инициализация менеджера файлов.
        
        Args:
            logger: Логгер для записи операций.
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def create_directory_structure(
        self,
        base_dir: Path,
        structure: Dict[str, str]
    ) -> Path:
        """
        Создание структуры директорий и файлов.
        
        Args:
            base_dir: Базовая директория.
            structure: Словарь с путями файлов и их содержимым.
        
        Returns:
            Path: Путь к созданной директории.
        """
        base_dir = Path(base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path, content in structure.items():
            full_path = base_dir / file_path
            
            # Создание родительских директорий
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Запись файла
            try:
                full_path.write_text(content, encoding="utf-8")
                self.logger.debug(f"Создан файл: {full_path}")
            except Exception as e:
                self.logger.error(f"Ошибка при создании файла {full_path}: {e}")
                raise
        
        return base_dir
    
    def ensure_directory(self, directory: Path) -> Path:
        """
        Создание директории, если она не существует.
        
        Args:
            directory: Путь к директории.
        
        Returns:
            Path: Путь к директории.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    def write_file(self, file_path: Path, content: str) -> None:
        """
        Запись содержимого в файл.
        
        Args:
            file_path: Путь к файлу.
            content: Содержимое файла.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        self.logger.debug(f"Записан файл: {file_path}")

