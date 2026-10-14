class ParameterMappingContainer:
    """Класс для хранения строки файла конфигуратора для маппинга параметров"""


    #region Приватные поля
    __aim_parameter_name : str
    """Целевой параметр для записи"""

    __parameter_type : str
    """Тип параметра (текст, целое число и пр.)"""

    __parameter_set : str
    """Целевой набор параметров"""

    __aim_ifc_class : str
    """Класс, которому будет назначен этот параметр"""

    __rule : str
    """Правило отбора элементов (помимо класса)"""

    __parameter_value : str
    """Значение параметра"""

    #endregion

    #region Публичные свойства (только для чтения)

    @property
    def aim_parameter_name(self) -> str:
        """Целевой параметр для записи"""
        return self.__aim_parameter_name

    @property
    def parameter_type(self) -> str:
        """Тип параметра (текст, целое число и пр.)"""
        return self.__parameter_type

    @property
    def parameter_set(self) -> str:
        """Целевой набор параметров"""
        return self.__parameter_set

    @property
    def aim_ifc_class(self) -> str:
        """Класс, которому будет назначен этот параметр"""
        return self.__aim_ifc_class

    @property
    def rule(self) -> str:
        """Правило отбора элементов (помимо класса)"""
        return self.__rule

    @property
    def parameter_value(self) -> str:
        """Значение параметра"""
        return self.__parameter_value

    #endregion

    def __init__(self, aim_parameter_name : str, parameter_type : str, parameter_set: str, 
                 aim_ifc_class : str, rule : str, parameter_value : str):
        """
        Инициализация контейнера маппинга параметров.

        Args:
            aim_parameter_name (str): Целевой параметр для записи.
            parameter_type (str): Тип параметра (текст, целое число и пр.).
            parameter_set (str): Целевой набор параметров.
            aim_ifc_class (str): Класс, которому будет назначен этот параметр.
            rule (str): Правило отбора элементов (помимо класса).
            parameter_value (str): Значение параметра.

        Raises:
            ValueError: Если любой из параметров равен None.
            TypeError: Если любой из параметров не является строкой.
        """

        # Проверка на None
        if aim_parameter_name is None:
            raise ValueError("aim_parameter_name не может быть None")
        if parameter_type is None:
            raise ValueError("parameter_type не может быть None")
        if parameter_set is None:
            raise ValueError("parameter_set не может быть None")
        if aim_ifc_class is None:
            raise ValueError("aim_ifc_class не может быть None")
        if rule is None:
            raise ValueError("rule не может быть None")
        if parameter_value is None:
            raise ValueError("parameter_value не может быть None")

        # Проверка на тип str
        if not isinstance(aim_parameter_name, str):
            raise TypeError("aim_parameter_name должен быть строкой")
        if not isinstance(parameter_type, str):
            raise TypeError("parameter_type должен быть строкой")
        if not isinstance(parameter_set, str):
            raise TypeError("parameter_set должен быть строкой")
        if not isinstance(aim_ifc_class, str):
            raise TypeError("aim_ifc_class должен быть строкой")
        if not isinstance(rule, str):
            raise TypeError("rule должен быть строкой")
        if not isinstance(parameter_value, str):
            raise TypeError("parameter_value должен быть строкой")

        self.__aim_parameter_name = aim_parameter_name
        self.__parameter_type = parameter_type
        self.__parameter_set = parameter_set
        self.__aim_ifc_class = aim_ifc_class
        self.__rule = rule
        self.__parameter_value = parameter_value
