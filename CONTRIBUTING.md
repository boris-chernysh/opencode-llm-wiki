# Вклад в opencode-llm-wiki

## Настройка
git clone https://github.com/<user>/opencode-llm-wiki.git
cd opencode-llm-wiki

## Тестирование
./tests/run-tests.sh

## Линтинг
pip install ruff
ruff check agent/scripts/ tests/

## Процесс
1. Форк + ветка
2. Изменения + тесты
3. `ruff check` зелёный
4. PR с заполненным шаблоном

## Стиль кода
- Python 3.8+, stdlib only
- snake_case, типизация по желанию
- Русские комментарии и строки OK
