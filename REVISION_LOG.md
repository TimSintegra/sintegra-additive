# REVISION_LOG.md

## Общий статус проекта

На дату 2026-08-20 выполнена базовая SEO-оптимизация главной страницы, добавлены технические файлы для поисковых систем и созданы 3 коммерческие посадочные страницы (3D-печать металлом, 3D-сканирование, изготовление по образцу/реверс-инжиниринг). На дату 2026-08-18 выполнено обновление дизайна и функциональности сайта Синтегра 3D. Изменения затронули:

- Дизайн-систему: CSS-переменные, анимации, glassmorphism, техно-эффекты
- Первый экран (Hero): тёмная тема, техно-сетка, объёмное изображение принтера
- Блок сравнения «Пластик | Металл»: интерактивные карточки с переключателями материалов
- Изображения: замена на версии с прозрачным фоном (логотип, принтер HBD P400)
- Исправление атрибутов `srcset` и `onerror` для изображений с прозрачным фоном
- Исправление адреса Яндекс Карт на главной странице (`index.html`)
- Восстановление стилей на странице `printing.html` под единый стандарт с главной
- Документация: добавлен настоящий отчёт о ревизии

Все ссылки, атрибуты `alt`, `width`, `height`, классы и стили элементов сохранены без изменений.

---

## Список изменённых файлов

### 1. `index.html` — базовая SEO-оптимизация и H1

**Добавлено в `<head>`:**
- `<link rel="canonical" href="https://sintegra-additive.ru/">`
- OpenGraph-теги: `og:type=website`, `og:title`, `og:description`, `og:image` (HBD P400), `og:url`
- `twitter:card=summary_large_image` для корректного превью в соцсетях

**Изменено в `<head>`:**
- `<title>`: `3D-печать металлом и пластиком на заказ | Синтегра 3D`
- `<meta name="description">`: промышленная 3D-печать металлом и пластиком, SLM/LPBF, FDM, сканирование, моделирование, реверс-инжиниринг, регионы и расчёт стоимости

**Изменено в Hero-блоке:**
- H1: `Промышленная 3D-печать металлом и пластиком`
- Бренд `Синтегра 3D — аддитивное производство` вынесен в надзаголовок (`.hero__badge`)

---

### 2. `robots.txt`

**Изменено:**
- Блокировка служебных директорий: `Disallow: /api/`, `Disallow: /tools/`
- Разрешение индексации всего остального: `Allow: /`
- Указана ссылка на Sitemap: `https://sintegra-additive.ru/sitemap.xml`

---

### 3. `sitemap.xml`

**Добавлено:**
- Текущие страницы: `/`, `printing.html`, `equipment.html`, `scanning.html`, `modeling.html`, `portfolio.html`, `contacts.html` с атрибутами `lastmod`, `changefreq` и `priority`
- Планируемые страницы: `about.html`, `blog.html`, `privacy.html`
- Пространство имён `http://www.sitemaps.org/schemas/sitemap/0.9`

---

### 4. `3d-pechat-metallom/index.html` (новый файл — посадочная «3D-печать металлом»)

**Добавлено:**
- Title: `3D-печать металлом на заказ (SLM/LPBF) | Синтегра 3D`
- H1: `3D-печать металлом на заказ`
- Мета-описание: SLM/LPBF печать из титана, алюминия, нержавеющей стали на HBD P400
- OpenGraph + canonical, единые шапка/футер/модалка/скрипты из `index.html`
- Блоки: Hero с кнопкой «Запросить расчёт», «Что печатаем» (сетка применений), «Технические характеристики HBD P400» (`.spec-table`), «Используемые материалы» (интерактивный `.materials` пикер), форма загрузки модели/ТЗ (`.form`, `data-form`)
- Использованы классы `css/style.css`: `hero hero--dark techno-grid ambient-glow`, `section`, `card`, `grid--3`, `spec-table`, `materials`, `form`

---

### 5. `3d-skanirovanie/index.html` (новый файл — посадочная «3D-сканирование»)

**Добавлено:**
- Title: `3D-сканирование деталей на заказ в Татарстане и РФ | Синтегра 3D`
- H1: `3D-сканирование деталей и оборудования`
- Мета-описание с акцентом на точность до ±0,024 мм и объекты до 4 м
- Блоки: Hero, акцент на точность (±0,024 мм, до 4 м), области применения (сетка), примеры работ (`.gallery`), форма заявки (`.form`, `data-form`)
- Использованы классы `css/style.css`: `hero`, `card`, `grid--3`, `gallery`, `form`

---

### 6. `izgotovlenie-po-obrazcu/index.html` (новый файл — посадочная «Изготовление по образцу / реверс-инжиниринг»)

**Добавлено:**
- Title: `Изготовление деталей по образцу и реверс-инжиниринг | Синтегра 3D`
- H1: `Изготовление деталей по физическому образцу`
- Воронка (4 шага): Физический образец → 3D-сканирование → CAD-модель → 3D-печать (`.grid--4` + `.card`)
- Блок «Что вы получаете» (сетка преимуществ), форма заявки (`.form`, `data-form`)
- Использованы классы `css/style.css`: `hero`, `card`, `grid--4`, `grid--3`, `form`

---

### 7. `css/style.css`

**Добавлено:**
- CSS-переменные индустриальной темы:
  - `--bg-dark: #0B0F17` — тёмный фон
  - `--bg-transition: #161B26` — переходный фон
  - `--cold: #F8FAFC` — холодный акцентный цвет
  - `--accent: #0066FF` — основной акцент
  - `--accent-2: #3385ff` — дополнительный акцент
- Служебные классы:
  - `.techno-grid` — техно-сетка на фоне через `linear-gradient`
  - `.ambient-glow` — мягкое синее свечение через `radial-gradient`
  - `.glass` — стеклянная карточка с `backdrop-filter: blur(16px)`, мягкими тенями и полупрозрачной границей
  - `.glass--dark` — тёмная вариация glass-карточки
- Стили для тёмного Hero-блока (`.hero--dark`):
  - Фон `var(--bg-dark)` вместо `var(--graphite)`
  - Усиленный 3D-эффект изображения: `scale(1.12)`, увеличенные отрицательные отступы
  - Реалистичная тень `drop-shadow(0 40px 70px rgba(0,0,0,.55))`
  - Мягкое синее свечение через `radial-gradient` с `rgba(0,102,255,.22)`
  - Адаптация мета-информации под тёмную тему
- Стили для интерактивных карточек сравнения:
  - `.compare-cards` — сетка для двух карточек
  - `.compare-card` — объёмная карточка с hover-эффектами
  - `.compare-card--plastic` / `.compare-card--metal` — тематические вариации
  - `.compare-card--metal::before` — металлическая градиентная рамка через `mask-composite`
  - `.compare-card__tabs`, `.compare-tab` — переключатели материалов
  - `.compare-card__specs`, `.compare-spec` — сетка характеристик
  - Адаптив: на мобильных карточки складываются в одну колонку, `.compare-spec` становится одноколоночным

**Изменено:**
- Все анимации и переходы переведены с `ease` на `cubic-bezier(0.4, 0, 0.2, 1)`
- У логотипов в шапке (`.header__logo img`) и футере (`.footer__logo img`) добавлен `object-fit: contain` для предотвращения деформации
- Hero grid placeholder в тёмном режиме: `background: transparent` вместо градиента

---

### 8. `index.html`

**Добавлено:**
- Классы `hero--dark techno-grid ambient-glow` к первому экрану для активации тёмной темы, техно-сетки и свечения
- Блок сравнения «Пластик | Металл» переработан в 2 крупные объёмные карточки:
  - **Карточка «Пластик»** с переключателями: PLA, PETG, ABS, TPU, PA, PC
  - **Карточка «Металл»** с переключателями: Сталь, Титан, Алюминий, Inconel, Кобальт-хром
  - Каждая карточка содержит изображение, заголовок, описание, переключатели материалов, таблицу характеристик и кнопку
- Атрибуты `data-compare-tabs="plastic"` и `data-compare-tabs="metal"` для инициализации JS-скрипта
- Атрибуты `data-plastic-field` и `data-metal-field` у полей характеристик для динамического обновления

**Изменено:**
- Заменены пути к изображениям:
  - `/img/logo.png` → `/img/logo-removebg-preview.png`
  - `/img/hbd-p400.jpg` → `/img/hbd-p400-removebg-preview.png`

**Сохранено без изменений:**
- Все ссылки на кнопках (`/equipment.html`, `/printing.html#plastic`, `/printing.html#metal`, `tel:+788555244830`, `#`)
- Атрибуты `alt`, `width`, `height`, `srcset`, `sizes`, `onerror`, `loading`
- Классы элементов

---

### 9. `js/main.js`

**Добавлено:**
- Объект `plasticData` с характеристиками материалов PLA, PETG, ABS, TPU, PA, PC
- Объект `metalData` с характеристиками материалов Сталь, Титан, Алюминий, Inconel, Кобальт-хром
- Скрипт инициализации переключателей сравнения:
  - Обработка кликов по `.compare-tab`
  - Динамическое обновление текста в `.compare-spec__value` при смене материала
  - Поддержка двух типов полей: `data-plastic-field` и `data-metal-field`

---

### 10. `contacts.html`

**Изменено:**
- Заменён путь к логотипу: `/img/logo.png` → `/img/logo-removebg-preview.png`

---

### 11. `printing.html`

**Изменено:**
- Заменены пути к изображениям:
  - `/img/logo.png` → `/img/logo-removebg-preview.png`
  - `/img/hbd-p400.jpg` → `/img/hbd-p400-removebg-preview.png`

---

### 12. `equipment.html`

**Изменено:**
- Заменены пути к изображениям:
  - `/img/logo.png` → `/img/logo-removebg-preview.png`
  - `/img/hbd-p400.jpg` → `/img/hbd-p400-removebg-preview.png`

---

### 13. `scanning.html`

**Изменено:**
- Заменён путь к логотипу: `/img/logo.png` → `/img/logo-removebg-preview.png`

---

### 14. `modeling.html`

**Изменено:**
- Заменён путь к логотипу: `/img/logo.png` → `/img/logo-removebg-preview.png`

---

### 15. `portfolio.html`

**Изменено:**
- Заменён путь к логотипу: `/img/logo.png` → `/img/logo-removebg-preview.png`

---

### 16. `tools/gen-images.py`

**Изменено:**
- Заменено имя файла в скрипте генерации: `hbd-p400.jpg` → `hbd-p400-removebg-preview.png`

---

### 17. `img/logo-removebg-preview.png` (новый файл)

**Добавлено:**
- Версия логотипа с прозрачным фоном ( `.png` )

---

### 18. `img/hbd-p400-removebg-preview.png` (новый файл)

**Добавлено:**
- Изображение принтера HBD P400 с прозрачным фоном ( `.png` )

---

### 19. `index.html`, `printing.html`, `equipment.html` — исправление атрибутов изображений

**Проблема:** Браузер игнорировал `src` и загружал старый WEBP-файл из `srcset`, из-за чего изображение HBD P400 отображалось с белым фоном, несмотря на замену `src` на PNG с прозрачным фоном. Кроме того, атрибут `onerror` ссылался на устаревший файл `hbd-p400-cutout.png`.

**Изменено:**
- Удалён устаревший `srcset="/img/hbd-p400.webp 768w" sizes="(max-width: 768px) 90vw, ..."` у всех изображений HBD P400
- Удалён устаревший `onerror="this.onerror=null;this.src='/img/hbd-p400-cutout.png'"` у всех изображений HBD P400
- Проверено: у логотипа и других обновлённых изображений нет атрибутов `srcset`, `<picture>` или `<source>`, указывающих на старые файлы

**Затронутые файлы:**
- `index.html` — 3 изображения HBD P400 (hero, сравнение металл, блок оборудования)
- `printing.html` — 2 изображения HBD P400 (сравнение металл, блок оборудования)
- `equipment.html` — 1 изображение HBD P400 (hero)

---

### 20. `index.html` — исправление адреса Яндекс Карт

**Проблема:** На главной странице в блоке с Яндекс Картой отображался старый адрес «БСИ 5.2» (в URL — фрагмент `%D0%91%D0%A1%D0%98`), хотя на `contacts.html` адрес уже был исправлен на `Республика Татарстан, г. Нижнекамск, ул. Заводская, 3В`.

**Изменено:**
- Заменён `<iframe src="...">` на корректный из `contacts.html` с адресом `ул. Заводская, 3В`
- Исправлены ссылки «Открыть в Яндекс Картах» и «Построить маршрут» — удалён фрагмент `%D0%91%D0%A1%D0%98` (БСИ) из URL
- Текстовые упоминания старого адреса в `index.html` отсутствуют

---

### 21. `printing.html` — восстановление стилей под единый стандарт

**Проблема:** На странице 3D-печати «слетели» стили (CSS применялся частично). Блок сравнения «Пластик | Металл» использовал старые классы, которые больше не присутствуют в обновлённом `css/style.css`.

**Изменено:**
- Подключение таблицы стилей проверено: `<link rel="stylesheet" href="/css/style.css">` — корректно
- Блок сравнения переведён на новые классы из `css/style.css`:
  - `.compare` → `.compare-cards`
  - `.compare__col` → `.compare-card`
  - `.compare__photo` → `.compare-card__media`
  - `.compare__body` → `.compare-card__body`
  - `.compare__rows` → `.compare-card__specs`
  - `.compare__media` → `.compare-card__gallery`
  - `.compare__foot` → `.compare-card__foot`
  - `.compare__vs` удалён (не используется в новом дизайне)
- Добавлены интерактивные переключатели материалов с атрибутами `data-compare-tabs="plastic"` и `data-compare-tabs="metal"`
- Добавлены новые поля для JS: `data-plastic-field` и `data-metal-field`
- Удалены пустые/битые атрибуты `srcset` у изображений HBD P400
- Удалены мини-галереи `.compare-card__gallery` из обеих карточек для лаконичности
- Переработаны стили карточек: фиксированная высота медиа `260px`, `object-fit: contain`, компактные табы-чипсы, разделительные линии в спецификациях, приглушённые лейблы
- Добавлен тёмный градиентный фон для медиа-блока пластиковой карточки (`#161B26`)
- Обновлена мобильная адаптивность: `gap: 24px`, спецификации одноколоночные

**Затронутые файлы:**
- `printing.html` — удалены галереи, обновлён блок сравнения
- `css/style.css` — переработаны стили `.compare-card__media`, `.compare-tab`, `.compare-card__specs`, удалён `.compare-card__gallery`

---

### 22. JSON-LD микроразметка (Schema.org) на страницах сайта

**Добавлено:**
- `index.html` — блок `<script type="application/ld+json">` с типами `Organization` + `LocalBusiness`:
  - `name`: Синтегра 3D
  - `address`: Республика Татарстан, Нижнекамск, ул. Заводская, 3В (`PostalAddress`)
  - `description`: промышленная 3D-печать металлом и пластиком, 3D-сканирование, реверс-инжиниринг
  - `telephone`, `email`, `areaServed` (Татарстан, Россия), `logo`, `image`, `url`
- `contacts.html` — аналогичная микроразметка `Organization` + `LocalBusiness`
- `3d-pechat-metallom/index.html` — микроразметка `Service`:
  - `serviceType`: Промышленная 3D-печать металлом (SLM/LPBF)
  - `provider`: Синтегра 3D, `areaServed`: Татарстан, Россия
- `3d-skanirovanie/index.html` — микроразметка `Service`:
  - `serviceType`: Высокоточное 3D-сканирование деталей и оборудования
  - `provider`: Синтегра 3D, `areaServed`: Татарстан, Россия

---

### 23. Исправление sitemap.xml и канонических тегов

**Проблема (по SITE_STRUCTURE_AUDIT.md):** `sitemap.xml` содержал 3 несуществующие страницы (`about.html`, `blog.html`, `privacy.html` — ведут на 404) и не содержал 3 реальные посадочные страницы; канонические теги отсутствовали на 6 базовых страницах и на посадочной `izgotovlenie-po-obrazcu`.

**Изменено в `sitemap.xml`:**
- Удалены несуществующие URL: `/about.html`, `/blog.html`, `/privacy.html`
- Добавлены реальные посадочные страницы (priority 0.9, changefreq monthly):
  - `https://sintegra-additive.ru/3d-pechat-metallom/`
  - `https://sintegra-additive.ru/3d-skanirovanie/`
  - `https://sintegra-additive.ru/izgotovlenie-po-obrazcu/`
- Итого в sitemap: 10 фактических страниц сайта

**Добавлено `<link rel="canonical">` в `<head>`:**
- `printing.html` → `https://sintegra-additive.ru/printing.html`
- `scanning.html` → `https://sintegra-additive.ru/scanning.html`
- `modeling.html` → `https://sintegra-additive.ru/modeling.html`
- `equipment.html` → `https://sintegra-additive.ru/equipment.html`
- `portfolio.html` → `https://sintegra-additive.ru/portfolio.html`
- `contacts.html` → `https://sintegra-additive.ru/contacts.html`
- `izgotovlenie-po-obrazcu/index.html` → `https://sintegra-additive.ru/izgotovlenie-po-obrazcu/`

**Итог:** канонический тег проставлен ровно 1 раз на каждой из 10 страниц сайта.

---

### 24. Интеграция посадочных страниц в глобальную навигацию и блоки главной

**Проблема (по SITE_STRUCTURE_AUDIT.md):** 3 посадочные страницы (`/3d-pechat-metallom/`, `/3d-skanirovanie/`, `/izgotovlenie-po-obrazcu/`) были недоступны из шапки, подвала и блоков услуг главной — страницы-«сироты».

**Изменено во всех 10 HTML-страницах:**
- `<nav class="header__nav">` — добавлены 3 ссылки (итого 9 пунктов):
  - `3D-печать металлом` → `/3d-pechat-metallom/`
  - `3D-сканирование` → `/3d-skanirovanie/`
  - `Изготовление по образцу` → `/izgotovlenie-po-obrazcu/`
- `<ul class="footer__nav">` (колонка «Разделы») — добавлены те же 3 прямые ссылки (итого 7 пунктов).

**Изменено в `index.html`:**
- Блок сравнения «Металл»: кнопка «Подробнее о металле» → `/3d-pechat-metallom/` (было `/printing.html#metal`)
- Блок «3D-сканирование»: кнопка «Подробнее о сканировании» → `/3d-skanirovanie/` (было `/scanning.html`)
- Блок «3D-моделирование»: добавлена кнопка «Изготовление по образцу» → `/izgotovlenie-po-obrazcu/` (рядом с «Подробнее о моделировании»)

---

### 25. Микроразметка Service на `izgotovlenie-po-obrazcu/index.html`

**Проблема (по SITE_STRUCTURE_AUDIT.md):** на посадочной странице `/izgotovlenie-po-obrazcu/` отсутствовала JSON-LD разметка (на остальных посадочных и главной/контактах она уже была).

**Добавлено в `<head>`:**
- `<script type="application/ld+json">` с типом `Service`:
  - `name`: Изготовление деталей по физическому образцу и реверс-инжиниринг
  - `serviceType`: Изготовление деталей по физическому образцу и реверс-инжиниринг
  - `description`: Изготовление деталей по образцу: 3D-сканирование, восстановление CAD-модели и 3D-печать металлом или пластиком.
  - `provider`: Синтегра 3D
  - `areaServed`: Татарстан, Россия
  - `url`: https://sintegra-additive.ru/izgotovlenie-po-obrazcu/

**Итог:** микроразметка Schema.org теперь присутствует на 5 из 10 страниц (главная, контакты — Organization+LocalBusiness; 3 посадочные — Service).

---

### 26. Нормализация шапки: выпадающее меню «Услуги» и компактная навигация

**Проблема:** в шапке было 9 пунктов меню, из-за чего навигация переполняла контейнер, ссылки перекрывали логотип и обрезали телефон справа.

**Изменено в `css/style.css`:**
- Контейнер `.container`: `padding: 0 20px` (было `24px`), `max-width: 1200px` сохранён
- `.header__inner`: добавлен `justify-content: space-between`, `position: relative` для центрирования навигации
- `.header__nav`: `position: absolute; left: 50%; transform: translateX(-50%); gap: 16px` (было `margin-left: auto; gap: 26px`)
- Стили dropdown: `.dropdown`, `.dropdown-menu` с плавным появлением, тенью и `z-index: 1000`
- Адаптив: на `max-width: 768px` dropdown превращается в раскрывающийся блок внутри мобильного меню, управляется кликом

**Изменено в `js/main.js`:**
- Добавлен обработчик клика по `.dropdown-toggle` для мобильных: переключает класс `.is-open` на `.dropdown`

**Изменено во всех 10 HTML-страницах:**
- Навигация сокращена с 9 пунктов до 5: `[ Главная ] [ Услуги ▾ ] [ Оборудование ] [ Портфолио ] [ Контакты ]`
- Под «Услуги» вынесен выпадающий список с 5 ссылками:
  - 3D-печать (все материалы) → `/printing.html`
  - 3D-печать металлом → `/3d-pechat-metallom/`
  - 3D-сканирование → `/3d-skanirovanie/`
  - 3D-моделирование → `/modeling.html`
  - Изготовление по образцу → `/izgotovlenie-po-obrazcu/`

**Затронутые файлы:**
- `css/style.css`
- `js/main.js`
- `index.html`, `printing.html`, `equipment.html`, `contacts.html`, `modeling.html`, `portfolio.html`, `scanning.html`
- `3d-skanirovanie/index.html`, `3d-pechat-metallom/index.html`, `izgotovlenie-po-obrazcu/index.html`

---

## Инструкция по откату

Если необходимо вернуться к предыдущему состоянию проекта, используйте Git:

### Полный откат до состояния до изменений

```bash
# Переключиться на предыдущий коммит
git checkout HEAD~1

# Или откатить последний коммит, сохранив изменения в рабочей директории
git reset --soft HEAD~1

# Или полностью удалить все изменения (необратимо!)
git reset --hard HEAD
git clean -fd
```

### Откат только определённых файлов

```bash
# Восстановить конкретный файл из последнего коммита
git checkout HEAD~1 -- css/style.css
git checkout HEAD~1 -- index.html
# и т.д.
```

### Откат только изображений

```bash
# Удалить новые файлы с прозрачным фоном
git rm --cached img/logo-removebg-preview.png
git rm --cached img/hbd-p400-removebg-preview.png

# Восстановить старые изображения (если они были в репозитории)
git checkout HEAD~1 -- img/logo.png img/hbd-p400.jpg
```

### Просмотр истории коммитов

```bash
git log --oneline --all
```

### Откат к конкретному коммиту

```bash
# Найти хэш нужного коммита
git log --oneline

# Переключиться на него
git checkout <хэш-коммита>

# Или создать новую ветку от этого коммита
git checkout -b <имя-ветки> <хэш-коммита>
```

---

## Комментарии

- Все изменения сохранены в отдельных атомарных коммитах по логическим блокам
- Исходные файлы изображений (`logo.png`, `hbd-p400.jpg`) оставлены в репозитории
- Новые изображения с прозрачным фоном добавлены как дополнительные файлы
- Структура проекта и все остальные файлы остались без изменений
