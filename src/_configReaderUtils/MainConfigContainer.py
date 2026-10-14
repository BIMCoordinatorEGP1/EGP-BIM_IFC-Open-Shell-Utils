class MainConfigContainer:
    """Класс для хранения основной конфигурации утилиты"""

    #region Приватные поля

    __model_file_paths : list[str]
    """Ссылки на IFC модели для обработки"""

    __output_folder_path : str
    """Ссылка для сохранения обработанных IFC моделей"""

    __parameter_mapping_config_file_path : str
    """Ссылка на файл с конфигурацией маппинга параметров"""

    #endregion

    #region Публичные поля (только чтение)

    @property
    def model_file_paths(self) -> list[str]:
        """Ссылки на IFC модели для обработки"""
        return self.__model_file_paths

    @property
    def output_folder_path(self) -> str:
        """Ссылка для сохранения обработанных IFC моделей"""
        return self.__output_folder_path

    @property
    def parameter_mapping_config_file_path(self) -> str:
        """Ссылка на файл с конфигурацией маппинга параметров"""
        return self.__parameter_mapping_config_file_path

    #endregion

    def __init__(self, model_file_paths : list[str], output_folder_path : str, parameter_mapping_config_file_path : str):

        """
        Инициализирует контейнер основной конфигурации утилиты.

        Args:
            model_file_paths: Список путей к IFC-моделям для обработки.
            output_folder_path: Путь к папке для сохранения обработанных моделей.
            parameter_mapping_config_file_path: Путь к файлу конфигурации маппинга параметров.

        Raises:
            TypeError: Если хотя бы один из аргументов имеет неверный тип или равен None.
        """
        # Проверка на None
        if model_file_paths is None:
            raise TypeError("model_file_paths не может быть None")
        if output_folder_path is None:
            raise TypeError("output_folder_path не может быть None")
        if parameter_mapping_config_file_path is None:
            raise TypeError("parameter_mapping_config_file_path не может быть None")

        # Проверка типов
        if not isinstance(model_file_paths, list):
            raise TypeError("model_file_paths должен быть списком (list[str])")
        for idx, path in enumerate(model_file_paths):
            if not isinstance(path, str):
                raise TypeError(
                    f"Элемент model_file_paths с индексом {idx} должен быть строкой, получен {type(path).__name__}"
                )
        if not isinstance(output_folder_path, str):
            raise TypeError("output_folder_path должен быть строкой (str)")
        if not isinstance(parameter_mapping_config_file_path, str):
            raise TypeError("parameter_mapping_config_file_path должен быть строкой (str)")

        # Присваивание значений приватным полям
        self.__model_file_paths = model_file_paths
        self.__output_folder_path = output_folder_path
        self.__parameter_mapping_config_file_path = parameter_mapping_config_file_path