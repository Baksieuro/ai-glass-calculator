# Разбор кодовой базы ai_glass_calculator

Документ для ясности по каждой части проекта: назначение файлов, строк, связей. Используется для рефакторинга и внесения изменений.

---

## Рефакторинг (актуальная структура)

- **Пути:** единый источник — `app.config.settings`: PROJECT_ROOT, DATA_DIR, PDF_DIR, TEMPLATES_DIR, STATIC_DIR, ASSETS_DIR, LOGO_DIR, WORKS_DIR. БД: `data/app.db`. PDF: `pdf/`.
- **Тексты:** `data/texts.json` (ошибки, подписи позиций); загрузка через `get_texts()`. Реквизиты: `data/company_info.json` или дефолт в коде — `get_company_info()`.
- **Валидация:** `app.core.validators` — validate_dimensions, validate_product_key, validate_material_price, validate_drill_price.
- **Ассеты:** `app.core.assets` — get_logo_file_uri(), get_works_file_uris(); используются в pdf_routes и pdf_generator.
- **Удалено:** `app/core/image_tools.py`, `app/templates/calc_result.html`.

---

## 1. Структура проекта

```
ai_glass_calculator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI, роутеры, static из settings
│   ├── config.py            # Settings (пути, лимиты), get_texts(), get_company_info(), DELIVERY_TERMS и др.
│   ├── db.py                # SQLAlchemy, DATA_DIR из settings
│   ├── models.py
│   ├── crud.py
│   ├── test_calc.py
│   ├── api/routes.py
│   ├── core/
│   │   ├── schemas.py
│   │   ├── calculator.py    # calc(), response_to_pdf_data(), load_products(), load_json(); validators + texts
│   │   ├── validators.py    # validate_dimensions, validate_product_key, validate_material_price, validate_drill_price
│   │   ├── assets.py        # get_logo_file_uri(), get_works_file_uris()
│   │   └── pdf_generator.py # generate_pdf(); пути и ассеты из config/assets
│   ├── web/                 # manager_routes, pdf_routes, history_routes — пути из settings
│   ├── templates/
│   └── assets/
├── data/
│   ├── company_info.json
│   ├── texts.json           # errors, positions, units
│   ├── prices_materials.json
│   ├── prices_services.json
│   └── products.txt
├── pdf/
├── scripts/
├── requirements.txt
└── README.md
```

---

## 2. Точка входа и роутинг

### app/main.py

| Строка | Назначение |
|--------|------------|
| 1–4 | Импорт FastAPI, StaticFiles, Jinja2Templates, Path. |
| 7–10 | Импорт settings, API router, manager_router, pdf_router. **history_router не импортирован и не подключён** — маршруты /manager/history* не работают. |
| 13 | Создание приложения FastAPI с title из settings. |
| 16 | `BASE_DIR` — каталог `app/` (родитель от `__file__`). |
| 17 | Монтирование `/static` на `app/static`. **Папки `app/static` нет** — при первом запросе к /static возможна ошибка или 404. |
| 18 | Jinja2: шаблоны из `app/templates`. Переменная `templates` используется только в index(); роуты в web/ создают свой Jinja2Templates с тем же путём. |
| 20–22 | GET `/`: рендер `index.html`. **Файла `index.html` в templates нет** — при заходе на / будет ошибка. |
| 25–28 | Подключение роутеров: `/api` (API), manager_router и pdf_router без префикса. **history_router не подключён.** |

Итог: для работоспособности нужны index.html (или редирект на /manager), папка static (или убрать mount), подключение history_router.

---

## 3. Конфигурация

### app/config.py

| Строка | Назначение |
|--------|------------|
| 1–3 | pathlib.Path, typing (ClassVar, Dict, List), pydantic_settings.BaseSettings. |
| 6–7 | Класс Settings: PROJECT_NAME по умолчанию "AI Glass Calculator". |
| 9–10 | BASE_DIR = каталог app/; DATA_DIR = app/data. **Путь к данным:** данные лежат в корне проекта в `data/`, а не в `app/data/`. В calculator.py используется свой PROJECT_ROOT и DATA_DIR от корня проекта. |
| 12–13 | MODEL = "qwen" — зарезервировано под ИИ, в коде не используется. |
| 15–17 | ASSETS_DIR = app/assets, LOGO_DIR = app/assets/logo, WORKS_DIR = app/assets/works. |
| 20–21 | MAX_HEIGHT_MM = 1605, MAX_WIDTH_MM = 2750 — проверки в calculator.calc(). |
| 26–34 | COMPANY_INFO — ClassVar dict с реквизитами (дублирует data/company_info.json). |
| 36–53 | DELIVERY_TERMS, PAYMENT_TERMS, ADDITIONAL_TERMS, FINAL_TERMS — списки строк для PDF. |
| 55–56 | Config: env_file = ".env" для переопределения через переменные окружения. |
| 59 | Экземпляр settings. |

В pdf_routes.py используется `settings.LOGO_FILE` — в config такого атрибута нет, только LOGO_DIR. Нужно либо добавить LOGO_FILE (например первый файл из LOGO_DIR), либо в pdf_routes брать логотип из LOGO_DIR.

---

## 4. База данных

### app/db.py

| Строка | Назначение |
|--------|------------|
| 10–11 | BASE_DIR = родитель от db.py (каталог app/), DATA_DIR = app/data. **Фактически БД лежит в корне проекта data/app.db**, т.к. в других местах DATA_DIR считают от корня. Здесь DATA_DIR = BASE_DIR / "data" = app/data — возможна путаница с путём к БД. |
| 14–15 | Создание каталога data при отсутствии (mkdir). |
| 17–18 | DB_PATH = data/app.db, DATABASE_URL = sqlite:///... |
| 20–24 | create_engine с check_same_thread=False, echo=False. |
| 26–27 | SessionLocal, Base. |

Важно: если DATA_DIR в db.py трактуется как app/data, то app.db будет в app/data/app.db. Нужно сверить с scripts/create_db.py и реальным местом создания БД. В create_db.py BASE_DIR = parent.parent от скрипта = корень проекта, и в sys.path добавляется корень. Импорт `from app.db import engine, Base` использует app.db, т.е. engine создаётся из app/db.py, и DB_PATH там = BASE_DIR.parent / "data" было бы корректно для корня проекта, но в db.py BASE_DIR = parent от __file__ = app. Значит БД создаётся в app/data/app.db.

### app/models.py

| Строка | Назначение |
|--------|------------|
| 9–19 | Модель Proposal: id, proposal_number (уникальный), created_at, total, pdf_path (строка пути к файлу), items_json (текст JSON), deliveries_json (текст JSON), manager, status (draft/confirmed/cancelled). |

### app/crud.py

| Строка | Назначение |
|--------|------------|
| 9–28 | create_proposal(db, proposal_number, total, pdf_path, items, deliveries, manager, status): сериализация deliveries/items в JSON (ensure_ascii=False), создание Proposal, add/commit/refresh, возврат объекта. |
| 30–32 | list_proposals(db, limit=50, offset=0): запрос по Proposal, сортировка по created_at desc, offset/limit. |
| 34–35 | get_proposal(db, proposal_id): фильтр по id. |
| 37–38 | get_proposal_by_number(db, proposal_number): фильтр по номеру. |

---

## 5. Схемы запросов/ответов (API)

### app/core/schemas.py

| Строка | Назначение |
|--------|------------|
| 5–13 | CalcOptions: edge, film, drill, drill_qty, pack, delivery_city, mount — все с дефолтами, опции одного изделия. |
| 16–22 | CalcItemFull: product_key (обязательный), width_mm, height_mm, quantity=1, options=CalcOptions(). |
| 25–27 | CalcRequest: items — список CalcItemFull (основной вход API). |
| 30–37 | CalcPosition: name, quantity, unit, unit_price, total, item_index (Optional[int]) — одна строка в ответе калькулятора. |
| 40–43 | CalcResponse: positions (список CalcPosition), total. |

В test_calc.py используются имена CalcItem и CalcOptions; в schemas есть CalcItemFull и CalcOptions. CalcItem в schemas нет — тест сломан.

---

## 6. Калькулятор (ядро расчёта)

### app/core/calculator.py

| Строка | Назначение |
|--------|------------|
| 9–11 | BASE_DIR = app/core/, PROJECT_ROOT = app/, DATA_DIR = PROJECT_ROOT.parent / "data" = корень проекта / data. Данные читаются из корня проекта data/. |
| 15–17 | mm2m(v)=v/1000; calc_area(w,h)=м²; calc_perimeter(w,h)=периметр в м. |
| 20–22 | round_to_100_up(x): округление вверх до сотен (math.ceil(x/100)*100). |
| 25–38 | load_products(): читает data/products.txt; строки формата "name;thickness;key"; комментарии (#) и пустые пропускаются; возвращает dict[key] = {label, thickness}. |
| 41–43 | load_json(name): читает data/{name}. |
| 49–55 | calc(request): загружает products, prices_materials.json, prices_services.json; positions=[], grand_total=0. |
| 59–72 | Цикл по request.items: проверка height_mm/width_mm против settings.MAX_*; product по product_key; area, perimeter; mat_price из mat_prices; base_price_single = area*mat_price, округление вверх до 100; total_item = base_price_single*quantity; добавление позиции (материал) с item_index=idx. |
| 97–113 | Опция edge: цена за периметр из srv_prices["edge"], мин. 100; позиция "Обработка кромки", total_item +=. |
| 115–128 | Опция film и "mirror" в product_key: площадь * srv_prices["film"], мин. 100; позиция "Противоосколочная плёнка". |
| 131–147 | Опция drill: цена по толщине из srv_prices["drill"][t], drill_qty; позиция "Сверление отверстий". |
| 150–163 | Опция pack: площадь * srv_prices["pack"], мин. 100; "Упаковка в гофрокартон". |
| 166–178 | Опция mount: srv_prices["mount"]*area; "Монтаж (ориентировочно)". |
| 181–192 | total_item округляется вверх до 100; grand_total += total_item; позиция "Итого по изделию". |
| 195–209 | Доставка: delivery_city берётся из request.items[0].options (один раз); цена из srv_prices["delivery"][delivery_city]; позиция с item_index=None. |
| 211–216 | grand_total округляется вверх до 100; return CalcResponse(positions, total=grand_total). |

Важно: доставка привязана к первому изделию; если у первого нет delivery_city, доставка не добавляется.

---

## 7. API-роуты

### app/api/routes.py

| Строка | Назначение |
|--------|------------|
| 9 | APIRouter(tags=["Calculator"]). |
| 14–21 | POST /calculate: принимает CalcRequest, вызывает calc(request), возвращает result; при ошибке HTTP 400 с текстом. |
| 24–31 | POST /pdf: calc(request), затем generate_pdf(result). Но generate_pdf в pdf_generator принимает (items, deliveries, total, ...), а не CalcResponse. В api/routes передаётся result (CalcResponse) — несоответствие сигнатур, см. pdf_generator.generate_pdf. |

В pdf_generator.generate_pdf первый аргумент — items (list), не CalcResponse. Значит в api/routes при вызове generate_pdf(result) будет передаваться объект CalcResponse, а не список items — либо в pdf_generator нужно принимать result и извлекать result.positions/result.total и преобразовывать в items/deliveries, либо в routes перед вызовом строить items/deliveries из result. Сейчас в коде: `pdf_path = generate_pdf(result)` — без преобразования, значит generate_pdf должна уметь принимать CalcResponse или в routes баг.

Проверка pdf_generator.generate_pdf: сигнатура generate_pdf(items, deliveries, total, filename=..., ...). Значит в api/routes вызов generate_pdf(result) неверный: result — CalcResponse, а ожидается items (list). Это баг: нужно из result собрать items и deliveries и передать их в generate_pdf.

---

## 8. PDF-генератор

### app/core/pdf_generator.py

| Строка | Назначение |
|--------|------------|
| 21–25 | BASE_DIR = app/core/, TEMPLATES_DIR, ASSETS_DIR, DATA_DIR (здесь DATA_DIR = BASE_DIR / "data" = app/core/data — не корень! Ошибка пути к company_info.json, т.к. файл лежит в корне проекта data/). |
| 29–36 | company_info загружается из DATA_DIR / "company_info.json". При DATA_DIR = app/core/data файл не найдётся. Нужен путь к корню проекта data/. |
| 38–45 | _load_logo(): ищет первый файл в ASSETS_DIR/"logo" с расширением png/jpg/jpeg/webp/svg, возвращает file:/// URL. |
| 47–56 | _load_work_photos(): до 3 изображений из ASSETS_DIR/works. |
| 59–68 | Сигнатура generate_pdf(items, deliveries, total, filename, proposal_number, delivery_terms, payment_terms, additional_terms, final_terms). |
| 80–82 | logo, works через _load_logo/_load_work_photos. |
| 84–92 | Дефолты для filename, proposal_number по дате/времени. |
| 93–107 | Рендер commercial_blue.html с items, deliveries, total, company_info, terms, logo, works. |
| 110–117 | out_dir = settings.BASE_DIR (каталог app/), pdf_path = out_dir / filename. PDF сохраняется в app/, а не в pdf/. |
| 118–119 | HTML(string=html_out, base_url=BASE_DIR).write_pdf(str(pdf_path)). |

Несоответствия: DATA_DIR в pdf_generator указывает на app/core/data; сохранение PDF в settings.BASE_DIR (app/), тогда как pdf_routes сохраняет в pdf/ в корне проекта.

---

## 9. Веб-роуты менеджера

### app/web/manager_routes.py

| Строка | Назначение |
|--------|------------|
| 15–17 | Роутер без префикса, BASE_DIR = app/, templates = app/templates. |
| 19–26 | GET /manager: load_products(), рендер manager_form.html с products. |
| 29–53 | POST /manager/preview: Form data_json. Парсинг JSON, извлечение data["items"]. CalcRequest(items=items_payload), calc(req). При ошибке JSON/расчёта — HTML 400. |
| 55–86 | По result.positions строятся items_map по item_index: разбор name (формат "Label (4.0 мм) [2500 × 1000 мм]"), "Итого по изделию" → item_total, остальное → services. deliveries — позиции с item_index is None (доставка). |
| 96–104 | data_for_pdf = {items, deliveries, total}, data_json_out для передачи в форму превью и дальше в POST /manager/pdf. |
| 105–115 | Рендер manager_preview.html с result, items_list, deliveries, total, data_json. |

Формат name в калькуляторе: строка с "мм" и "[" — парсится через split; хрупко при смене формата в calculator.

---

## 10. Роуты PDF (менеджер)

### app/web/pdf_routes.py

| Строка | Назначение |
|--------|------------|
| 17–19 | BASE_DIR = app/, TEMPLATES_DIR = app/templates, PDF_DIR = корень проекта / pdf, mkdir. |
| 23–38 | POST /manager/pdf: Form data_json. Парсинг, items, deliveries, total. Номер КП = КП_{DDMMYYYYHHMMSS}, pdf_filename, pdf_path = PDF_DIR / pdf_filename. |
| 44–54 | Логотип: settings.LOGO_FILE — атрибут в config отсутствует (есть только LOGO_DIR). Works: перебор файлов в settings.WORKS_DIR. |
| 56–75 | Рендер commercial_blue.html с items, deliveries, total, company_info из settings, logo, works, terms из settings (списки). |
| 78–79 | WeasyPrint HTML(string=html).write_pdf(pdf_path). |
| 83–94 | SessionLocal(), create_proposal(..., pdf_path=pdf_filename), db.close(). |
| 96–103 | Возврат templates.TemplateResponse("manager_pdf_ready.html", ...). **Шаблона manager_pdf_ready.html нет** в templates — ошибка рендера. |
| 106–119 | GET /manager/pdf/download/{filename}: FileResponse из PDF_DIR. |

Шаблон commercial_blue.html в pdf_routes получает delivery_terms, payment_terms, additional_terms как списки (из config), а в шаблоне выводится {{ delivery_terms }} — будет вывод списка в одну строку. Для красивого PDF лучше передавать строки (join) или в шаблоне цикл по списку.

---

## 11. Роуты истории

### app/web/history_routes.py

| Строка | Назначение |
|--------|------------|
| 15–18 | router, BASE_DIR, templates, PDF_DIR = app.parent / "pdf" (корень проекта/pdf). |
| 21–28 | GET /manager/history: list_proposals(db, limit=200), рендер history_list.html. |
| 30–45 | GET /manager/history/{proposal_id}: get_proposal, парсинг items_json/deliveries_json, рендер history_view.html. |
| 48–53 | GET /manager/history/download/{filename}: FileResponse из PDF_DIR. |

Роутер не подключён в main.py — эти маршруты сейчас не работают.

---

## 12. Шаблоны

- **manager_form.html** — форма: динамическое добавление блоков товаров (product_key, width_mm, height_mm, quantity, опции). При отправке собирается JSON { items } в data_json, POST на /manager/preview.
- **manager_preview.html** — вывод позиций по изделиям, доставка, итог; форма с data_json на POST /manager/pdf.
- **commercial_blue.html** — основной шаблон КП: реквизиты, изделия (product_name, thickness, width, height, quantity, services, item_total), доставка, блок "Наши работы" (works), условия (delivery_terms, payment_terms, additional_terms, final_terms), итог. Ожидает одиночные строки для terms; в pdf_routes передаются списки.
- **calc_result.html** — шаблон под один товар (product_name, thickness, width, height, services, total) и реквизиты; в текущих роутах не используется.
- **history_list.html** — таблица КП (id, номер, дата, итог, ссылки "Открыть" и "Скачать PDF"). pdf_path в БД хранится как имя файла (например КП_….pdf), split('/')[-1] даёт то же имя.
- **history_view.html** — одна КП: изделия, доставка, ссылка на скачивание PDF.

---

## 13. Данные (data/)

- **products.txt** — строки "Название;толщина;product_key" (калькулятор берёт первые 3 поля).
- **prices_materials.json** — ключи product_key, значения цена за м².
- **prices_services.json** — edge, film, drill (по толщинам "4","5","6","8"), pack, delivery (center_центр, suburb_пригород), mount (число).
- **company_info.json** — name, address, inn, rs, bank, bik, ks (используется в pdf_generator при корректном DATA_DIR; в pdf_routes берётся из settings.COMPANY_INFO).

---

## 14. Прочие файлы

- **app/core/image_tools.py** — load_logo(), load_work_images(limit=3) с random.sample; в проекте нигде не импортируется.
- **app/test_calc.py** — использует CalcItem, CalcOptions, CalcRequest(item=..., options=...). В schemas есть CalcItemFull и CalcRequest(items=[...]). Нужно заменить на CalcItemFull и CalcRequest(items=[item]), убрать передачу options отдельно (они внутри CalcItemFull).

---

## 15. Сводка багов и несоответствий (и что исправлено)

1. **main.py** — исправлено: GET `/` теперь редирект на `/manager`; `/static` монтируется только если папка существует; подключён `history_router`.
2. **pdf_routes.py** — исправлено: логотип берётся из первого файла в `settings.LOGO_DIR` (без LOGO_FILE); добавлен шаблон `manager_pdf_ready.html`.
3. **pdf_generator.py** — без изменений: DATA_DIR по-прежнему app/core/data (company_info может не находиться, если файл в корне data/); сохранение PDF в settings.BASE_DIR (app/). API PDF теперь идёт через response_to_pdf_data + generate_pdf(items, deliveries, total).
4. **api/routes.py** — исправлено: расчёт → `response_to_pdf_data(result)` → `generate_pdf(items=..., deliveries=..., total=...)`.
5. **commercial_blue.html** — исправлено: условия (delivery_terms, payment_terms, additional_terms) поддерживают и строку, и список (цикл по списку).
6. **test_calc.py** — исправлено: используется CalcItemFull, CalcRequest(items=[item]), delivery_city="center_центр".
7. **manager_form.html** — не исправлялось: в форме по-прежнему нет поля delivery_city; доставка в расчёте не добавится, пока в options не будет delivery_city (можно добавить select в форму).

Дальше при рефакторинге: выровнять пути к data/ (config vs calculator vs db), вынести общую логику парсинга result.positions в один модуль (сейчас дублируется в manager_routes и response_to_pdf_data).
