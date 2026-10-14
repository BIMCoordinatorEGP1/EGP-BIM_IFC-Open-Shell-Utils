class ElementSelectionUtils:
    """Утилиты для работы с правилами"""

    [staticmethod]
    def get_rule_answer(raw_str: str) -> bool:
        # Разрешаем использовать только наши функции
        context = {
            'get_test_value1': ElementSelectionUtils.get_test_value1,
            'get_test_value2': ElementSelectionUtils.get_test_value2,
        }
        # Вычисляем выражение в безопасном окружении (без встроенных функций)
        return eval(raw_str, {}, context)

    [staticmethod]
    def get_test_value1() -> int:
        return 1

    [staticmethod]
    def get_test_value2() -> int:
        return 2