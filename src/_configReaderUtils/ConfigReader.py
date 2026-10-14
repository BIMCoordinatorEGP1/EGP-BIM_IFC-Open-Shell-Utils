import csv
from pathlib import Path

from _configReaderUtils.ParameterMappingContainer import ParameterMappingContainer
from _configReaderUtils.MainConfigContainer import MainConfigContainer

class ConfigReader:
    """Утилиты для чтения конфигураторов"""

    @staticmethod
    def read_main_config(folder_path : str) -> MainConfigContainer:
        """
        Читает конфигурационные файлы из указанной папки и возвращает настроенный экземпляр MainConfigContainer.

        Ожидаемые файлы в папке:
            ModelsPathsConfig.txt – список путей к IFC-моделям (одна модель на строку)
            OutputPathConfig.txt   – путь к папке для сохранения результатов (одна строка)
            ParameterMappingConfig.txt – путь к .tsv файлу с маппингом параметров (одна строка)

        Правила разбора каждого файла:
            - Строки, начинающиеся с '##', считаются комментариями и игнорируются.
            - Пустые строки, а также строки, состоящие только из пробельных символов, игнорируются.
            - Оставшиеся строки обрезаются от ведущих/замыкающих пробелов и используются как пути.

        Требования к содержимому:
            - В ModelsPathsConfig.txt должна быть хотя бы одна значимая строка. Каждый путь должен указывать на
              существующий файл с расширением .ifc.
            - В OutputPathConfig.txt должна быть ровно одна значимая строка. Она должна указывать на существующую
              директорию.
            - В ParameterMappingConfig.txt должна быть ровно одна значимая строка. Она должна указывать на
              существующий файл с расширением .tsv.

        Args:
            folder_path: Путь к папке, содержащей конфигурационные файлы.

        Returns:
            Экземпляр MainConfigContainer с прочитанными настройками.

        Raises:
            FileNotFoundError: Если папка folder_path не существует, или какой-либо из файлов/директорий,
                               указанных в конфигурациях, не найден.
            ValueError: Если нарушены правила формата (неверное количество значимых строк, некорректное расширение,
                        отсутствие значимых строк, папка не является директорией).
        """
        base_dir = Path(folder_path)
        if not base_dir.exists():
            raise FileNotFoundError(f"Папка конфигурации не существует: {folder_path}")
        if not base_dir.is_dir():
            raise ValueError(f"Указанный путь не является директорией: {folder_path}")

        # Чтение ModelsPathsConfig.txt
        models_file = base_dir / "ModelsPathsConfig.txt"
        if not models_file.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {models_file}")

        model_paths = ConfigReader._read_config_lines(models_file)
        if not model_paths:
            raise ValueError("ModelsPathsConfig.txt не содержит значимых строк (путей к моделям)")

        # Проверка каждого пути модели
        validated_model_paths: list[str] = []
        for raw_path in model_paths:
            p = Path(raw_path)
            if not p.exists():
                raise FileNotFoundError(f"IFC-модель не найдена: {raw_path}")
            if p.suffix.lower() != ".ifc":
                raise ValueError(f"Файл модели должен иметь расширение .ifc: {raw_path}")
            validated_model_paths.append(str(p.resolve()))

        # Чтение OutputPathConfig.txt
        output_file = base_dir / "OutputPathConfig.txt"
        if not output_file.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {output_file}")

        output_lines = ConfigReader._read_config_lines(output_file)
        if len(output_lines) != 1:
            raise ValueError(
                "OutputPathConfig.txt должен содержать ровно одну значимую строку (путь к папке для результатов)"
            )
        output_path_str = output_lines[0]
        output_path = Path(output_path_str)
        if not output_path.exists():
            raise FileNotFoundError(f"Целевая папка не существует: {output_path_str}")
        if not output_path.is_dir():
            raise ValueError(f"Путь в OutputPathConfig.txt должен указывать на директорию: {output_path_str}")

        # Чтение ParameterMappingConfig.txt
        mapping_file = base_dir / "ParameterMappingConfig.txt"
        if not mapping_file.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {mapping_file}")

        mapping_lines = ConfigReader._read_config_lines(mapping_file)
        if len(mapping_lines) != 1:
            raise ValueError(
                "ParameterMappingConfig.txt должен содержать ровно одну значимую строку (путь к .tsv файлу)"
            )
        mapping_path_str = mapping_lines[0]
        mapping_path = Path(mapping_path_str)
        if not mapping_path.exists():
            raise FileNotFoundError(f"Файл маппинга параметров не найден: {mapping_path_str}")
        if mapping_path.suffix.lower() != ".tsv":
            raise ValueError(f"Файл маппинга параметров должен иметь расширение .tsv: {mapping_path_str}")

        return MainConfigContainer(
            model_file_paths=validated_model_paths,
            output_folder_path=str(output_path.resolve()),
            parameter_mapping_config_file_path=str(mapping_path.resolve())
        )

    @staticmethod
    def _read_config_lines(file_path: Path) -> list[str]:
        """
        Читает текстовый файл конфигурации, возвращает список значимых непустых строк (без комментариев).
        """
        lines = []
        with open(file_path, 'r', encoding='ANSI') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith('##'):
                    continue
                lines.append(line)
        return lines

    @staticmethod
    def read_parameter_mapping_config(file_path : str) -> list[ParameterMappingContainer]:
        """
        Читает файл конфигурации маппинга параметров (TSV) и возвращает список контейнеров.

        Args:
            file_path (str): Абсолютный путь к файлу.

        Returns:
            List[ParameterMappingContainer]: Список успешно разобранных контейнеров.

        Raises:
            ValueError: Если путь равен None, или файл не соответствует ожидаемой схеме.
            FileNotFoundError: Если файл не найден.
            PermissionError: Если недостаточно прав для чтения файла.

        Файл должен иметь TSV-формат со следующей структурой:
        - Первая строка — заголовок (игнорируется).
        - Последующие строки — данные со столбцами:
          Aim Parameter Name, Parameter Type, Parameter Set, Classes, Rule, Parameter Value.
        Строки, в которых первый столбец начинается с '##', пропускаются.
        При ошибках в отдельных строках сообщение выводится в консоль, и чтение продолжается.
        """

        if file_path is None:
            raise ValueError("file_path не может быть None")

        containers: list[ParameterMappingContainer] = []
        data_line_encountered = False

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                
                # Читаем заголовок (первая строка)
                try:
                    header = next(reader)
                except StopIteration:
                    # Файл пуст
                    raise ValueError("Файл не соответствует схеме: пустой файл, заголовок отсутствует")
                
                # Номер строки (заголовок = 1)
                line_number = 1
                
                # Обрабатываем строки данных
                for row in reader:
                    line_number += 1
                    data_line_encountered = True
                    
                    # Пропускаем полностью пустые строки
                    if not any(row):
                        continue
                    
                    # Проверка первого столбца на начало с '##'
                    if row and row[0].startswith('##'):
                        continue
                    
                    # Проверка количества столбцов (должно быть 6)
                    if len(row) != 6:
                        print(f"Ошибка в строке {line_number}: неверное количество столбцов "
                              f"(ожидается 6, получено {len(row)})")
                        continue
                    
                    try:
                        container = ParameterMappingContainer(
                            aim_parameter_name=row[0],
                            parameter_type=row[1],
                            parameter_set=row[2],
                            aim_ifc_class=row[3],
                            rule=row[4],
                            parameter_value=row[5]
                        )
                        containers.append(container)
                    except (ValueError, TypeError) as e:
                        print(f"Ошибка в строке {line_number}: {e}")
                        continue
                        
        except FileNotFoundError:
            # Пробрасываем стандартное исключение
            raise
        except PermissionError:
            raise
        except Exception as e:
            # Другие ошибки чтения — оборачиваем в пояснение, но сохраняем тип для ясности
            raise IOError(f"Ошибка при чтении файла: {e}") from e

        # Если были строки данных, но ни одна не обработана успешно — ошибка схемы
        if data_line_encountered and not containers:
            raise ValueError("Файл не соответствует схеме: ни одна строка данных не была успешно обработана")

        return containers