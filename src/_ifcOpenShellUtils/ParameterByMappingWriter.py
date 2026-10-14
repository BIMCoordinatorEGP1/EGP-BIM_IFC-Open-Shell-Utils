import os
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
import ifcopenshell.util.element as ifc_element
from ifcopenshell import entity_instance
from ifcopenshell.sql import sqlite_entity

from collections.abc import Mapping

from _configReaderUtils.ConfigReader import ConfigReader
from _configReaderUtils.ParameterMappingContainer import ParameterMappingContainer
from _configReaderUtils.MainConfigContainer import MainConfigContainer

class ParameterByMappingWriter:
    """Утилита для записи параметров с маппингом"""

    _TYPE_ALIASES = {
        "text": "IfcText",
        "label": "IfcLabel",
        "identifier": "IfcIdentifier",
        "description": "IfcText",
        "boolean": "IfcBoolean",
        "bool": "IfcBoolean",
        "logical": "IfcLogical",
        "integer": "IfcInteger",
        "int": "IfcInteger",
        "count": "IfcCountMeasure",
        "real": "IfcReal",
        "number": "IfcReal",
        "float": "IfcReal",
        "length": "IfcLengthMeasure",
        "positivelength": "IfcPositiveLengthMeasure",
        "area": "IfcAreaMeasure",
        "volume": "IfcVolumeMeasure",
    }

    _STRING_TYPES = {"IfcText", "IfcLabel", "IfcIdentifier", "IfcDescription"}
    _BOOL_TYPES = {"IfcBoolean"}
    _LOGICAL_TYPES = {"IfcLogical"}
    _INT_TYPES = {"IfcInteger", "IfcCountMeasure"}
    _REAL_TYPES = {"IfcReal", "IfcNumericMeasure", "IfcLengthMeasure", "IfcPositiveLengthMeasure", "IfcAreaMeasure", "IfcVolumeMeasure", }
    BASE_PARAMETERS_MARKER = "IfcBaseParameters"


    main_config : MainConfigContainer
    param_mapping_config : list[ParameterMappingContainer]

    def __init__(self, main_config_directory_path : str):
        """Инициализирует writer: читает основной конфиг и конфиг маппинга параметров.

        Args:
            main_config_directory_path: путь к директории с основным конфигурационным файлом.
        """

        # читаем основной конфигуратор
        self.main_config = ConfigReader.read_main_config(main_config_directory_path)

        # читаем файл с маппингом параметров
        self.param_mapping_config = ConfigReader.read_parameter_mapping_config(self.main_config.parameter_mapping_config_file_path)

    def on_write(self):
        """Запускает запись параметров по всем моделям, указанным в основном конфиге.

        Последовательно обрабатывает каждый файл модели из
        ``self.main_config.model_file_paths``, вызывая ``on_write_single``.
        """

        # выполняем работы в моделях по одной
        for path in self.main_config.model_file_paths:
            self.on_write_single(path, self.main_config.output_folder_path)

    def on_write_single(self, ifc_file_path : str, save_path_folder : str):
        """Записывает параметры в одну конкретную IFC-модель.

        Открывает файл модели и для каждого маппинга из ``param_mapping_config``
        отбирает подходящие по классу и правилу элементы.

        Args:
            ifc_file_path: путь к IFC-файлу модели.
        """

        # открываем модель
        ifc_file = ifcopenshell.open(ifc_file_path)

        # производим запись параметров
        for mapping in self.param_mapping_config:
            # получаем необходимые элементы
            elements_in_type = ifc_file.by_type(mapping.aim_ifc_class)
            on_write_elements = self.get_filtered_elements(elements_in_type, mapping.rule)

            # записываем параметры по маппингу
            self.set_parameter_by_map(ifc_file, on_write_elements, mapping.parameter_set, mapping.aim_parameter_name, 
                                      mapping.parameter_type, mapping.parameter_value)

        # сохраняем под исходным именем в целевой директории
        os.makedirs(save_path_folder, exist_ok=True)
        file_name = os.path.basename(ifc_file_path)
        save_path = os.path.join(save_path_folder, file_name)
        ifc_file.write(save_path)
        

    @staticmethod
    def set_parameter_by_map(ifc_file, ifc_elements : list, parameter_set : str, parameter_name : str, parameter_type : str, parameter_value : str):
        """Вычисляет и записывает параметр в pset для каждого элемента списка.

        ``parameter_value`` — строка с python-выражением (по аналогии с
        правилом фильтрации в ``get_filtered_elements``), которое
        компилируется один раз и вычисляется для каждого элемента.
        Внутри выражения доступны: 

        - ``elem`` — сам IFC-элемент;
        - ``info`` — результат ``elem.get_info()``;
        - ``psets`` — ленивая обёртка над pset'ами элемента (``LazyPsets``).

        Выражение может быть как явным литералом ("Пример текстового
        значения"), так и вычисляться из других параметров, например:
        ``psets['Dimensions']['DWO_Высота проема'] * psets['Dimensions']['DWO_Ширина проема']``.

        ``parameter_type`` задаёт целевой IFC-тип значения. Поддерживаются
        как короткие алиасы ("text", "real", "boolean", "integer",
        "logical"), так и точные имена IFC-типов ("IfcLabel",
        "IfcLengthMeasure" и т.п.) — см. ``_TYPE_ALIASES``.

        Ошибки на отдельном элементе (в вычислении выражения, приведении
        типа или записи в IFC) не прерывают обработку остальных элементов
        маппинга — такой элемент просто пропускается с сообщением в лог.

        Args:
            ifc_elements: элементы, в которые нужно записать параметр.
            parameter_set: имя набора свойств (Pset), в который пишем.
            parameter_name: имя свойства внутри набора.
            parameter_type: имя IFC-типа значения (алиас или точное имя).
            parameter_value: python-выражение, вычисляющее значение параметра.
        """

        func_code = compile(
            f"def _value_func(elem, info, psets): return ({parameter_value})",
            "<parameter_value>",
            "exec",
        )
        namespace = {}
        exec(func_code, namespace)
        value_func = namespace["_value_func"]

        for elem in ifc_elements:
            info = elem.get_info()
            psets = LazyPsets(elem)
            gid = info.get("GlobalId", "?")

            try:
                raw_value = value_func(elem, info, psets)
            except Exception as e:
                print(f'[{gid}] не удалось вычислить значение "{parameter_name}": {e}')
                continue

            try:
                value = ParameterByMappingWriter._cast_value(raw_value, parameter_type)
            except Exception as e:
                print(f'[{gid}] не удалось привести "{parameter_name}" к типу {parameter_type}: {e}')
                continue

            try:
                ParameterByMappingWriter._write_parameter(ifc_file, elem, parameter_set, parameter_name, value, parameter_type)
            except Exception as e:
                print(f'[{gid}] не удалось записать "{parameter_name}" в "{parameter_set}": {e}')
                continue


    @staticmethod
    def get_filtered_elements(ifc_elements : list, rule : str) -> list:
        """Отбирает из списка IFC-элементов те, что удовлетворяют правилу.

        Правило — строка с python-выражением, которое компилируется в функцию
        вида ``_rule_func(elem, info, psets)`` и вычисляется для каждого элемента.
        Внутри выражения доступны переменные:

        - ``elem`` — сам IFC-элемент;
        - ``info`` — результат ``elem.get_info()``;
        - ``psets`` — pset'ы элемента (см. ``LazyPsets``), подгружаются лениво.

        Элементы, на которых вычисление правила выбросило исключение, пропускаются.

        Args:
            ifc_elements: итерируемая коллекция IFC-элементов для фильтрации.
            rule: строка с python-выражением, возвращающим значение, приводимое к bool.

        Returns:
            list: элементы, для которых правило вернуло True.
        """
        output = []

        func_code = compile(
            f"def _rule_func(elem, info, psets): return bool({rule})",
            "<rule>",
            "exec"
        )

        namespace = {}
        exec(func_code, namespace)
        rule_func = namespace["_rule_func"]

        for elem in ifc_elements:
            info = elem.get_info()
            psets = LazyPsets(elem)
            try:
                if rule_func(elem, info, psets):
                    output.append(elem)
            except:
                continue
        return output

    @staticmethod
    def _normalize_type(parameter_type: str) -> str:
        """Приводит алиас типа к точному имени IFC-типа, если он известен."""
        key = parameter_type.strip().lower()
        return ParameterByMappingWriter._TYPE_ALIASES.get(key, parameter_type)

    @staticmethod
    def _cast_value(raw_value, parameter_type: str):
        """Приводит вычисленное значение к python-типу, соответствующему IFC-типу.

        Raises:
            ValueError / TypeError: если значение нельзя привести к
                ожидаемому типу (например, строка не парсится как число).
        """
        ifc_type = ParameterByMappingWriter._normalize_type(parameter_type)

        if ifc_type in ParameterByMappingWriter._STRING_TYPES:
            return str(raw_value)

        if ifc_type in ParameterByMappingWriter._BOOL_TYPES:
            return bool(raw_value)

        if ifc_type in ParameterByMappingWriter._LOGICAL_TYPES:
            # IfcLogical допускает TRUE/FALSE/UNKNOWN
            return None if raw_value is None else bool(raw_value)

        if ifc_type in ParameterByMappingWriter._INT_TYPES:
            return int(round(float(raw_value)))

        if ifc_type in ParameterByMappingWriter._REAL_TYPES:
            return float(raw_value)

        # неизвестный/явно не покрытый тип — отдаём значение как есть
        return raw_value

    @staticmethod
    def _write_parameter(ifc_file, elem, parameter_set: str, parameter_name: str, value, parameter_type : str):
        """Записывает значение параметра в элемент.

        Если ``parameter_set`` равен ``ParameterByMappingWriter.BASE_PARAMETERS_MARKER``
        ("IfcBaseParameters"), параметр — это не свойство из pset'а, а прямой
        атрибут самого IFC-элемента (например, ``elem.Name``,
        ``elem.Description``, ``elem.Tag``). В этом случае значение
        записывается через ``setattr`` напрямую в сущность, минуя механизм
        pset'ов.

        Во всех остальных случаях поведение прежнее: создаёт (при
        отсутствии) pset с именем ``parameter_set`` и записывает/обновляет
        в нём свойство ``parameter_name``.

        Raises:
            AttributeError: если ``parameter_name`` не является допустимым
                атрибутом схемы IFC для данного типа элемента.
        """

        if parameter_set == ParameterByMappingWriter.BASE_PARAMETERS_MARKER:
            # прямая запись в атрибут элемента, а не в pset
            if not hasattr(elem, parameter_name):
                raise AttributeError(
                    f'У элемента {elem.is_a()} нет базового атрибута "{parameter_name}"'
                )
            setattr(elem, parameter_name, value)
            return

        ifc_value = ParameterByMappingWriter._to_ifc_value(ifc_file, value, parameter_type)

        existing = ifcopenshell.util.element.get_pset(elem, parameter_set, should_inherit=False)
        if existing is None:
            pset_entity = ifcopenshell.api.run(
                "pset.add_pset", ifc_file, product=elem, name=parameter_set
            )
        else:
            pset_entity = ifc_file.by_id(existing["id"])

        ifcopenshell.api.run(
            "pset.edit_pset",
            ifc_file,
            pset=pset_entity,
            properties={parameter_name: ifc_value},
        )

    @staticmethod
    def _to_ifc_value(ifc_file, python_value, parameter_type: str):
        """Оборачивает python-значение в IFC-сущность точного типа из маппинга.
 
        Обёртка обеспечивает явное приведение типа: если передать в
        ``pset.edit_pset`` голый python-примитив, ifcopenshell сам решает,
        каким IFC-типом его представить (например, любая python ``str``
        без обёртки станет ``IfcLabel``, независимо от того, что в
        маппинге был указан "text" или "identifier"). Создавая сущность
        нужного типа заранее, мы гарантируем, что в pset попадёт именно
        тот тип, что задан в конфиге.
 
        ``None`` пропускается как есть — это сигнал для ``pset.edit_pset``
        удалить/обнулить свойство, а не значение, которое можно обернуть
        в IFC-тип.
 
        Args:
            ifc_file: открытая IFC-модель, в которой создаётся сущность.
            python_value: значение, уже приведённое ``_cast_value`` к
                нужному python-типу.
            parameter_type: имя IFC-типа значения (алиас или точное имя).
 
        Raises:
            RuntimeError: если ``parameter_type`` не является известным
                IFC-типом в схеме данной модели (например, опечатка в
                конфиге или неизвестный алиас).
        """
        if python_value is None:
            return None
 
        ifc_type = ParameterByMappingWriter._normalize_type(parameter_type)
        return ifc_file.create_entity(ifc_type, python_value)
    
class LazyPsets(Mapping):
    """Достаёт конкретный pset по имени только при обращении к нему.
    При полном переборе (items()/keys()/for ... in psets) один раз
    делает полный get_psets() и дальше работает с ним."""

    __slots__ = ("_elem", "_cache", "_full")

    def __init__(self, elem):
        """Создаёт ленивую обёртку над pset'ами элемента.

        Args:
            elem: IFC-элемент, для которого будут запрашиваться pset'ы.
        """

        self._elem = elem
        self._cache = {}
        self._full = None

    def __getitem__(self, key):
        """Возвращает pset по имени.

        Если полный набор pset'ов ещё не загружен, запрашивает только
        конкретный pset через ``ifc_element.get_pset`` и кеширует результат.

        Args:
            key: имя pset'а.

        Returns:
            Содержимое pset'а (обычно dict вида {свойство: значение}).

        Raises:
            KeyError: если pset с таким именем у элемента отсутствует.
        """

        if self._full is not None:
            return self._full[key]
        if key not in self._cache:
            result = ifc_element.get_pset(self._elem, key)
            if result is None:
                raise KeyError(key)
            self._cache[key] = result
        return self._cache[key]

    def _ensure_full(self):
        """Гарантирует, что полный набор pset'ов элемента загружен, и возвращает его.

        При первом вызове выполняет полный ``ifc_element.get_psets`` и
        сохраняет результат, при повторных — отдаёт уже закешированное значение.

        Returns:
            dict: полный набор pset'ов элемента.
        """

        if self._full is None:
            self._full = ifc_element.get_psets(self._elem)
        return self._full

    def __iter__(self):
        """Возвращает итератор по именам всех pset'ов элемента.

        Приводит к полной загрузке всех pset'ов через ``_ensure_full``.
        """

        return iter(self._ensure_full())

    def __len__(self):
        """Возвращает количество pset'ов у элемента.

        Приводит к полной загрузке всех pset'ов через ``_ensure_full``.
        """
        return len(self._ensure_full())

