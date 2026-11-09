# Инструмент визуализации графа зависимостей пакетов Ubuntu (apt)

**Вариант №23** (Дисциплина «Конфигурационное управление», МИРЭА 2026/2027).

Реализация инструмента командной строки для анализа и визуализации графа зависимостей пакетов менеджера Ubuntu (apt) без использования сторонних библиотек и пакетных менеджеров.

---

## 1. Общее описание

Приложение выполняет сбор данных о зависимостях пакетов, строит направленный граф зависимостей с помощью рекурсивного алгоритма поиска в ширину (BFS), вычисляет обратные зависимости, формирует спецификацию на языке Graphviz DOT и экспортирует итоговое графическое изображение в векторном формате SVG.

### Основные характеристики (Вариант 23)
* **Формат конфигурационного файла:** INI.
* **Формат пакетов:** Ubuntu (apt), парсинг индексов `Packages` и `Packages.gz`.
* **Алгоритм построения графа:** BFS (поиск в ширину) с рекурсией.
* **Фильтрация:** исключение пакетов, имя которых содержит заданную подстроку.
* **Корректная обработка циклов:** предотвращение бесконечной рекурсии и зацикливания.
* **Тестовый режим:** поддержка тестовых графов, где пакеты именуются заглавными латинскими буквами (`A: B, C`).
* **Дополнительная операция:** вычисление и вывод обратных зависимостей пакета (пакеты, зависящие от целевого) с повторным использованием рекурсивного BFS.
* **Визуализация:** формирование текстового описания Graphviz DOT и сохранение диаграммы в SVG (с поддержкой встроенного чистого рендерера без внешних утилит).

---

## 2. Описание всех функций и настроек

### 2.1. Конфигурационные параметры (файл INI)

Файл конфигурации содержит секцию `[settings]` со следующими обязательными параметрами:

| Параметр | Тип | Описание |
|---|---|---|
| `package_name` | строка | Имя анализируемого пакета (например, `curl` или `A`) |
| `repo_url` | строка | URL-адрес индекса `Packages`/`Packages.gz` или путь к локальному файлу репозитория |
| `test_mode` | boolean | Режим тестового репозитория (`true` или `false`) |
| `output_image` | строка | Путь к генерируемому SVG-файлу графа (должен оканчиваться на `.svg`) |
| `filter_substring` | строка | Подстрока для исключения пакетов из графа (или `none`/пусто) |

Пример конфигурационного файла:
```ini
[settings]
package_name = curl
repo_url = data/sample_ubuntu_packages.txt
test_mode = false
output_image = output.svg
filter_substring = none
```

### 2.2. Архитектура и модули

* **`src.config`**:
  * `load_config(file_path: str) -> AppConfig`: чтение и строгая валидация всех 5 параметров INI с генерацией понятных ошибок.
  * `AppConfig`: неизменяемая структура данных (dataclass) настроек.
* **`src.apt_parser`**:
  * `fetch_repository_text(url_or_path: str) -> str`: загрузка данных по HTTP/HTTPS или из локального файла, распаковка gzip при необходимости.
  * `clean_dependency_name(raw_token: str) -> str`: очистка имени пакета от версий `(...)`, альтернатив `|` и суффиксов архитектуры `:any`.
  * `parse_packages_index(content: str) -> Dict[str, List[str]]`: парсинг формата Debian/Ubuntu Packages в словарь смежности.
  * `get_direct_dependencies(pkg, repo) -> List[str]`: получение прямых зависимостей.
* **`src.graph`**:
  * `build_dependency_graph(start_package, repo, filter_substr) -> Dict[str, List[str]]`: рекурсивный BFS-обход графа зависимостей с отслеживанием посещенных вершин и фильтрацией.
  * `parse_test_repository(content: str) -> Dict[str, List[str]]`: парсинг файлов тестовых графов (заглавные латинские буквы).
  * `detect_cycles(graph) -> List[List[str]]`: нахождение и протоколирование циклов.
* **`src.reverse_deps`**:
  * `invert_graph(repo) -> Dict[str, List[str]]`: инвертирование ориентированных ребер графа.
  * `get_reverse_dependencies(target, repo, filter_substr) -> (direct, all_rev)`: нахождение пакетов, зависящих от целевого, с использованием алгоритма обхода BFS.
* **`src.visualizer`**:
  * `generate_graphviz_dot(root, graph) -> str`: генерация DOT-файла Graphviz.
  * `render_svg_native(root, graph) -> str`: генерация векторного SVG с вычислением послойного размещения вершин.
  * `export_graph_visualization(root, graph, svg_path)`: экспорт DOT и сохранение SVG.
* **`src.main`**:
  * Точка входа CLI с поддержкой аргументов командной строки `-c/--config` и `-s/--stage`.

---

## 3. Сборка проекта и запуск тестов

Проект реализован на стандартной библиотеке Python 3.11 (совместим с 3.8+) и не требует установки сторонних пакетов.

### Запуск через скрипты
* В Windows:
  ```cmd
  run.bat --config config.ini --stage 5
  ```
* В Linux / macOS:
  ```bash
  chmod +x run.sh
  ./run.sh --config config.ini --stage 5
  ```

### Запуск тестов
Запуск полного набора из 38 модульных и интеграционных тестов:
```bash
python -m unittest discover tests
```

### Запуск проверки качества кода (Линтер правил оформления)
Тест `test_code_style.py` автоматически валидирует соблюдение правил оформления репозитория:
* Длина каждой строки кода строго `<= 79` символов (Правило Р2).
* Длина каждой функции строго `<= 40` строк (Правило Ф1).
* Число аргументов функций `<= 7` (Правило А1).
* Отсутствие `#` комментариев вместо docstring-документации (Правило К1).
* Отсутствие магических чисел в сравнениях (Правило М1).

```bash
python -m unittest tests/test_code_style.py
```

---

## 4. Примеры использования

### 4.1. Этап 1: Минимальный прототип с конфигурацией
Выводит все настраиваемые пользователем параметры в формате ключ-значение:
```bash
python -m src.main --config config.ini --stage 1
```
Вывод:
```text
package_name: curl
repo_url: data/sample_ubuntu_packages.txt
test_mode: false
output_image: output.svg
filter_substring: none
```

### 4.2. Этап 2: Сбор данных
Извлекает и отображает прямые зависимости заданного пакета из репозитория:
```bash
python -m src.main --config config.ini --stage 2
```
Вывод:
```text
Direct dependencies for curl:
  - libc6
  - libcurl4
  - zlib1g
```

### 4.3. Этап 3: Основные операции (рекурсивный BFS)
Строит транзитивный граф зависимостей и выявляет циклы:
```bash
python -m src.main --config config_test.ini --stage 3
```
Вывод:
```text
Transitive dependency graph for A (BFS):
  A -> ['B', 'C']
  B -> ['D']
  C -> ['D']
  D -> []
Cycles detected: None
```

### 4.4. Этап 4: Дополнительные операции (Обратные зависимости)
Находит все пакеты, которые зависят от целевого пакета:
```bash
python -m src.main --config config_test.ini --stage 4
```
Вывод:
```text
Reverse dependencies for A:
  Direct reverse: []
  All (transitive) reverse: []
```

### 4.5. Этап 5: Визуализация (Graphviz DOT и SVG)
Генерирует DOT-спецификацию и формирует изображение графа в SVG:
```bash
python -m src.main --config config.ini --stage 5
```
Вывод:
```text
Graphviz DOT file generated: output.dot
SVG image generated: output.svg
digraph "curl" {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#EBF3FB", color="#1A73E8", fontname="Helvetica"];
  edge [color="#1A73E8", arrowhead=vee];
  "curl";
  "libc6";
  "libcurl4";
  "libgcc-s1";
  "libssl3";
  "zlib1g";
  "curl" -> "libc6";
  "curl" -> "libcurl4";
  "curl" -> "zlib1g";
  "libc6" -> "libgcc-s1";
  "libcurl4" -> "libc6";
  "libcurl4" -> "libssl3";
  "libcurl4" -> "zlib1g";
  "zlib1g" -> "libc6";
  "libgcc-s1" -> "libc6";
  "libssl3" -> "libc6";
}
```

---

## 5. Демонстрация трех различных пакетов

В каталоге `examples/` подготовлены конфигурации и сгенерированы визуализации для трех пакетов:

1. **`curl`** (`examples/config_curl.ini`):
   * Файлы: `examples/curl.dot`, `examples/curl.svg`.
   * Зависимости: `libc6`, `libcurl4`, `zlib1g`, `libssl3`, `libgcc-s1`.
2. **`git`** (`examples/config_git.ini`):
   * Файлы: `examples/git.dot`, `examples/git.svg`.
   * Зависимости: `libc6`, `libz1`, `git-man`, `libgcc-s1`.
3. **`nano`** (`examples/config_nano.ini`):
   * Файлы: `examples/nano.dot`, `examples/nano.svg`.
   * Зависимости: `libc6`, `libncursesw6`, `libtinfo6`, `libgcc-s1`.

Команда генерации всех трех примеров:
```bash
python -m src.main --config examples/config_curl.ini
python -m src.main --config examples/config_git.ini
python -m src.main --config examples/config_nano.ini
```

---

## 6. Сравнение со штатными инструментами пакетов Ubuntu

| Критерий | Разработанный инструмент | Штатные средства (`debtree`, `apt-cache`) |
|---|---|---|
| **Типы зависимостей** | Анализирует строго целевые зависимости поля `Depends` | `debtree` и `apt-cache` по умолчанию включают `Pre-Depends`, `Recommends`, `Suggests`, `Conflicts` |
| **Фильтрация** | Поддерживает пользовательскую фильтрацию по подстроке (`filter_substring`) | Штатные средства требуют внешних пайплайнов (`grep`, `awk`) или сложных регулярных выражений |
| **Альтернативы (`\|`)** | Автоматически выбирает дефолтный пакет-кандидат политики Debian | `debtree` отображает промежуточные ромбовидные OR-узлы |
| **Циклические зависимости** | Корректно определяет циклы и безопасно завершает обход BFS | `apt-rdepends` может дублировать ветви или зависеть от эвристик |
| **Автономность** | Работает без Graphviz и менеджера пакетов (чистый Python) | `debtree` жестко требует установленного `graphviz` и рабочей системы Debian/Ubuntu |

### Причины расхождений в результатах:
1. **Полнота графа:** Штатные утилиты (`apt-cache depends`) по умолчанию показывают рекомендуемые (`Recommends`) и предлагаемые (`Suggests`) пакеты, которые не являются строго обязательными для запуска приложения.
2. **Мультиархитектурность:** В Ubuntu утилиты отображают суффиксы архитектур (например, `libc6:amd64`). Разработанный инструмент нормализует имена для универсального отображения связей.
3. **Виртуальные пакеты:** Некоторые зависимости в apt являются виртуальными (например, `mail-transport-agent`). Наш инструмент разрешает их к первичному конкретному пакету, указанному в дизъюнкции, что обеспечивает детерминированность графа.
