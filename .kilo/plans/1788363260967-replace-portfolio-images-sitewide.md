# План: заменить старые фото портфолио на новые на всех страницах

## Цель
На страницах сайта заменить старые изображения из серии `/img/print-*.png` на новый набор, использованный в `portfolio.html`:
- 14 JPG: `img/portfolio-1.jpg` … `img/portfolio-14.jpg`
- 2 HEIC→JPG: `img/portfolio-15.jpg`, `img/portfolio-16.jpg`
- 2 WebP: `img/portfolio-15.webp`, `img/portfolio-16.webp`

Все файлы уже созданы в `img/` (см. предыдущий шаг плана `1788355865677-portfolio-gallery-update.md`).

`img/print-1.png` переименовываем, так как он семантически принадлежит не серии `print-*` (используется как обложка блока «3D-печать» на главной), а не галерее портфолио.

## Затронутые файлы

### 1. `index.html`
- **Строка 169** — одиночное изображение в блоке «3D-печать» (service-block__media).
  - Было: `<img src="/img/print-1.png" ...>`
  - Станет: `<img src="/img/service-3d-print.png" ...>`
  - Остальные атрибуты (`alt`, `loading="lazy"`) — без изменений.
- **Строки 417–422** — галерея из 6 пластиковых изделий.
  - `print-5.png` → `portfolio-1.jpg`
  - `print-8.png` → `portfolio-2.jpg`
  - `print-7.png` → `portfolio-3.jpg`
  - `print-3.png` → `portfolio-4.jpg`
  - `print-4.png` → `portfolio-5.jpg`
  - `print-6.png` → `portfolio-6.jpg`
  - Подписи (`gallery__caption`), классы `reveal`, атрибуты `data-lightbox`, `loading="lazy"` — оставить без изменений.

### 2. `printing.html` (строки 398–409)
12 элементов: 9 пластик + 3 металл. Замены:
- `print-5.png` → `portfolio-1.jpg`
- `print-8.png` → `portfolio-2.jpg`
- `print-7.png` → `portfolio-3.jpg`
- `print-3.png` → `portfolio-4.jpg`
- `print-4.png` → `portfolio-5.jpg`
- `print-6.png` → `portfolio-6.jpg`
- `print-9.png` → `portfolio-7.jpg`
- `print-2.png` → `portfolio-8.jpg`
- `print-1.png` → `portfolio-9.jpg`  (см. п. 6: `print-1.png` уже будет переименован)
- `korpus-kompressora.jpg` (+`srcset`/`.webp`) → `portfolio-15.jpg` (атрибуты `srcset`, `sizes`, `width`, `height` убрать, оставить только `src` и `alt`)
- `photo_2026-06-24_14-54-05.jpg` (+`.webp` srcset) → `portfolio-10.jpg` (srcset/sizes/width/height убрать)
- `photo_2026-06-23_15-00-04.jpg` (+`.webp` srcset) → `portfolio-11.jpg` (srcset/sizes/width/height убрать)

Сохраняем атрибуты `data-category="plastic"` / `data-category="metal"`, `data-lightbox`, `loading="lazy"`, подписи.

### 3. `equipment.html`
**Не трогаем.** Строки 241–243 с `photo_2026-06-24_14-54-05.jpg`, `photo_2026-06-23_15-00-04.jpg`, `korpus-kompressora.jpg` оставляем как есть.

### 4. `3d-skanirovanie/index.html` (строки 203–208)
6 элементов. Замены:
- `print-5.png` → `portfolio-1.jpg`
- `print-7.png` → `portfolio-2.jpg`
- `print-3.png` → `portfolio-3.jpg`
- `print-4.png` → `portfolio-4.jpg`
- `print-6.png` → `portfolio-5.jpg`
- `korpus-kompressora.webp` → `portfolio-15.webp`

### 5. `portfolio.html`
Уже обновлён в предыдущем шаге. Проверок не требует.

### 6. Переименование файла `img/print-1.png`
- Команда: `mv img/print-1.png img/service-3d-print.png`
- Зачем: убрать файл из серии `print-*`, к которой относятся удаляемые изображения галереи.
- После переименования в `index.html:169` обновить `src` (см. п. 1). В `printing.html:406` этот файл больше не используется — там `src` заменяется на `portfolio-9.jpg`.

## Шаги реализации
1. Переименовать файл: `mv img/print-1.png img/service-3d-print.png`.
2. В `index.html:169` заменить `src="/img/print-1.png"` → `src="/img/service-3d-print.png"`.
3. В `index.html:417–422` заменить 6 `src` согласно п. 1.
4. В `printing.html:398–409` заменить 12 `src` согласно п. 2, попутно убрав `srcset`/`sizes`/`width`/`height` у трёх «металлических» элементов.
5. В `3d-skanirovanie/index.html:203–208` заменить 6 `src` согласно п. 4.
6. `equipment.html` — не изменять.
7. Валидация (см. ниже).

## Решения и допущения
- Подписи (`gallery__caption`) на затронутых страницах НЕ удаляем — пользователь просил убрать их только в `portfolio.html`. Текст подписей оставляем прежний.
- Нумерация соответствий `print-*` → `portfolio-*` выбрана по принципу «первые 9 фото из новой подборки для пластика, 10–11 для металла, 15 для корпуса компрессора». Семантически новые фото не привязаны к старым категориям.
- Атрибуты `data-category="plastic"` / `data-category="metal"` на `printing.html` сохраняем.
- `equipment.html` намеренно не трогаем — пользователь явно попросил оставить фото как есть.
- `img/print-1.png` переименовываем, потому что в `index.html` он семантически не относится к серии `print-*` (это обложка блока «3D-печать», а не элемент галереи).

## Валидация
- Открыть `index.html`, `printing.html`, `3d-skanirovanie/index.html` и убедиться, что изображения загружаются (нет 404 в DevTools).
- Проверить лайтбокс-клик на новых фото на `printing.html` (там есть `data-lightbox`).
- `grep` по `print-` в `*.html` — после изменений должны остаться **только** ссылки на `img/service-3d-print.png` (т.е. старое имя `print-1.png` исчезнет из HTML).
- `grep` по `korpus-kompressora` и `photo_2026-06-2[34]` в `*.html` — допустимы только в `equipment.html` (по решению пользователя) и в `3d-skanirovanie/index.html` (если там что-то осталось вне галереи — проверить отдельно; в текущем контексте упоминаний вне галереи нет).

## Вне области
- Удаление старых файлов из `img/` (`print-2.png` … `print-12.png`, `korpus-kompressora.jpg`, `photo_2026-06-23_15-00-04.*`, `photo_2026-06-24_14-54-05.*`, `korpus-kompressora-480w.webp`).
- Изменение подписей или структуры галерей.
- Оптимизация/ресайз новых изображений.
- Любые правки `equipment.html`.
