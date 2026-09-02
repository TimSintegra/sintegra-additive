# План обновления портфолио

## Задача
Заменить все фотографии в галерее `portfolio.html` на новые из папки `img/new/`, убрать фильтры по материалам и подписи.

## Файлы в `img/new/` (18 шт.)
- 14 JPG: `IMAGE 2026-09-02 HH:MM:SS.jpg` (с пробелами в имени)
- 2 HEIC: `IMG_3572.HEIC`, `IMG_3573.HEIC`
- 2 WebP: `korpus-kompressora-480w.webp`, `photo_2026-06-24_14-54-05.webp`

## Шаги реализации

### 1. Конвертация HEIC
- `IMG_3572.HEIC` → `/img/portfolio-15.jpg`
- `IMG_3573.HEIC` → `/img/portfolio-16.jpg`
- Команда macOS: `sips -s format jpg IMG_3572.HEIC --out /img/portfolio-15.jpg` (аналогично для IMG_3573)
- Альтернатива: пользователь конвертирует вручную через Preview или онлайн-сервис

### 2. Копирование остальных файлов
Скопировать 16 файлов (14 JPG + 2 WebP) из `img/new/` в `/img/` с новыми именами:
- `portfolio-1.jpg` … `portfolio-14.jpg`
- `portfolio-15.webp` (korpus-kompressora-480w.webp)
- `portfolio-16.webp` (photo_2026-06-24_14-54-05.webp)

### 3. Изменение `portfolio.html`
Заменить блок галереи (строки 76–101) на:

```html
  <!-- ======== Галерея ======== -->
  <section class="section">
    <div class="container">
      <div class="gallery" data-gallery>

        <div class="gallery__item reveal"><img src="/img/portfolio-1.jpg" alt="Проект 1" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-2.jpg" alt="Проект 2" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-3.jpg" alt="Проект 3" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-4.jpg" alt="Проект 4" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-5.jpg" alt="Проект 5" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-6.jpg" alt="Проект 6" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-7.jpg" alt="Проект 7" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-8.jpg" alt="Проект 8" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-9.jpg" alt="Проект 9" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-10.jpg" alt="Проект 10" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-11.jpg" alt="Проект 11" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-12.jpg" alt="Проект 12" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-13.jpg" alt="Проект 13" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-14.jpg" alt="Проект 14" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-15.jpg" alt="Проект 15" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-16.jpg" alt="Проект 16" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-15.webp" alt="Корпус компрессора" data-lightbox loading="lazy"></div>
        <div class="gallery__item reveal"><img src="/img/portfolio-16.webp" alt="Металлическое изделие HBD P400" data-lightbox loading="lazy"></div>

      </div>
    </div>
  </section>
```

### 4. Удалить неиспользуемые старые файлы (опционально)
- `/img/print-5.png`, `/img/print-2.png`, … `/img/print-12.png`, `/img/print-1.png`
- `/img/korpus-kompressora.jpg`, `/img/photo_2026-06-24_14-54-05.jpg`, `/img/photo_2026-06-23_15-00-04.jpg`

## Примечания
- JS-фильтр галереи в `main.js` (строки 132–147) продолжит работать, но так как кнопки фильтров удалены, пользователь увидит все 18 фото сразу.
- Подписи (`gallery__caption`) удалены, как просил пользователь. Их можно добавить позже.
- HEIC-файлы не поддерживаются в Chrome на Windows. Обязательна конвертация в JPG/WebP.
