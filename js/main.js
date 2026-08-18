document.addEventListener('DOMContentLoaded', function () {

  /* ---------- шапка при скролле ---------- */
  var header = document.querySelector('.header');
  var onScroll = function () {
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 10);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- мобильное меню ---------- */
  var burger = document.querySelector('.header__burger');
  if (burger) {
    burger.addEventListener('click', function () {
      document.body.classList.toggle('menu-open');
    });
    document.querySelectorAll('.header__nav a').forEach(function (a) {
      a.addEventListener('click', function () { document.body.classList.remove('menu-open'); });
    });
  }

  /* ---------- появление при скролле ---------- */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* ---------- вкладки ---------- */
  document.querySelectorAll('[data-tabs]').forEach(function (wrap) {
    var btns = wrap.querySelectorAll('.tabs__btn');
    var panels = wrap.querySelectorAll('.tabs__panel');
    btns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        btns.forEach(function (b) { b.classList.remove('is-active'); });
        btn.classList.add('is-active');
        panels.forEach(function (p) { p.classList.remove('is-active'); });
        var target = document.getElementById(btn.dataset.panel);
        if (target) target.classList.add('is-active');
      });
    });
  });

  /* ---------- сравнение: переключатели материалов ---------- */
  var plasticData = {
    pla: { equipment: 'Stereotech 530, Bambu Lab X1 Carbon', area: '300×300×300 и 256×256×256 мм', accuracy: 'слой от 0,05 мм', temp: '190–220 °C', strength: 'Средняя', applications: 'прототипы, корпуса, шестерни, мембраны, ролики' },
    petg: { equipment: 'Stereotech 530, Bambu Lab X1 Carbon', area: '300×300×300 и 256×256×256 мм', accuracy: 'слой от 0,05 мм', temp: '220–250 °C', strength: 'Высокая', applications: 'функциональные детали, посуда, детали для улицы' },
    abs: { equipment: 'Stereotech 530', area: '300×300×300 мм', accuracy: 'слой от 0,05 мм', temp: '230–260 °C', strength: 'Высокая', applications: 'оснастка, автодетали, корпуса' },
    tpu: { equipment: 'Stereotech 530', area: '300×300×300 мм', accuracy: 'слой от 0,05 мм', temp: '200–230 °C', strength: 'Гибкая', applications: 'прокладки, амортизаторы, ремни, шланги' },
    pa: { equipment: 'Stereotech 530', area: '300×300×300 мм', accuracy: 'слой от 0,05 мм', temp: '240–270 °C', strength: 'Очень высокая', applications: 'шестерни, подшипники, детали с трением' },
    pc: { equipment: 'Stereotech 530', area: '300×300×300 мм', accuracy: 'слой от 0,05 мм', temp: '260–300 °C', strength: 'Очень высокая', applications: 'прототипы, электротехника, детали с высокой нагрузкой' }
  };
  var metalData = {
    steel: { equipment: 'HBD P400, 4–6 лазеров 500/1000 Вт', area: '350×400×400 мм', accuracy: '0,05–0,2 мм · слой 20–120 мкм', density: '> 99,9%', hardness: 'Высокая', applications: 'корпуса, оснастка, детали с внутренними каналами' },
    titanium: { equipment: 'HBD P400, 4–6 лазеров 500/1000 Вт', area: '350×400×400 мм', accuracy: '0,05–0,2 мм · слой 20–120 мкм', density: '> 99,9%', hardness: 'Очень высокая', applications: 'авиация, медицина, высоконагруженные детали' },
    aluminum: { equipment: 'HBD P400, 4–6 лазеров 500/1000 Вт', area: '350×400×400 мм', accuracy: '0,05–0,2 мм · слой 20–120 мкм', density: '> 99,5%', hardness: 'Средняя', applications: 'автомобилестроение, радиаторы, корпуса' },
    inconel: { equipment: 'HBD P400, 4–6 лазеров 500/1000 Вт', area: '350×400×400 мм', accuracy: '0,05–0,2 мм · слой 20–120 мкм', density: '> 99,9%', hardness: 'Очень высокая', applications: 'турбины, двигатели, высокотемпературные узлы' },
    cobalt: { equipment: 'HBD P400, 4–6 лазеров 500/1000 Вт', area: '350×400×400 мм', accuracy: '0,05–0,2 мм · слой 20–120 мкм', density: '> 99,9%', hardness: 'Очень высокая', applications: 'стоматология, импланты, рабочие инструменты' }
  };
  document.querySelectorAll('[data-compare-tabs]').forEach(function (wrap) {
    var btns = wrap.querySelectorAll('.compare-tab');
    var type = wrap.dataset.compareTabs;
    var data = type === 'metal' ? metalData : plasticData;
    var fieldAttr = type === 'metal' ? 'data-metal-field' : 'data-plastic-field';
    btns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        btns.forEach(function (b) { b.classList.remove('is-active'); });
        btn.classList.add('is-active');
        var material = btn.dataset.material;
        var values = data[material];
        if (!values) return;
        wrap.querySelectorAll('[' + fieldAttr + ']').forEach(function (el) {
          var field = el.getAttribute(fieldAttr);
          if (values[field] !== undefined) el.textContent = values[field];
        });
      });
    });
  });

  /* ---------- выбор материала (металл) ---------- */
  document.querySelectorAll('[data-materials]').forEach(function (wrap) {
    var btns = wrap.querySelectorAll('.materials__btn');
    var panels = wrap.querySelectorAll('.materials__panel');
    btns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        btns.forEach(function (b) { b.classList.remove('is-active'); });
        btn.classList.add('is-active');
        panels.forEach(function (p) { p.classList.remove('is-active'); });
        var target = document.getElementById(btn.dataset.panel);
        if (target) target.classList.add('is-active');
      });
    });
  });

  /* ---------- аккордеон FAQ ---------- */
  document.querySelectorAll('[data-accordion]').forEach(function (wrap) {
    var items = wrap.querySelectorAll('.accordion__item');
    items.forEach(function (item) {
      var btn = item.querySelector('.accordion__btn');
      var body = item.querySelector('.accordion__body');
      btn.addEventListener('click', function () {
        var isOpen = item.classList.contains('is-open');
        items.forEach(function (it) { it.classList.remove('is-open'); });
        document.querySelectorAll('.accordion__body').forEach(function (b) { b.style.maxHeight = '0px'; });
        if (!isOpen) {
          item.classList.add('is-open');
          body.style.maxHeight = body.scrollHeight + 'px';
        }
      });
    });
  });

  /* ---------- фильтр галереи ---------- */
  document.querySelectorAll('[data-gallery]').forEach(function (gallery) {
    var filters = gallery.querySelectorAll('.gallery__filter button');
    var items = gallery.querySelectorAll('.gallery__item');
    filters.forEach(function (f) {
      f.addEventListener('click', function () {
        filters.forEach(function (x) { x.classList.remove('is-active'); });
        f.classList.add('is-active');
        var cat = f.dataset.filter;
        items.forEach(function (item) {
          var match = cat === 'all' || item.dataset.category === cat;
          item.classList.toggle('gallery--hide', !match);
        });
      });
    });
  });

  /* ---------- лайтбокс галереи ---------- */
  var lightbox = document.querySelector('.lightbox');
  if (lightbox) {
    var lbImg = lightbox.querySelector('img');
    var closeLb = function () { lightbox.classList.remove('is-open'); };
    lightbox.querySelector('.lightbox__close').addEventListener('click', closeLb);
    lightbox.addEventListener('click', function (e) { if (e.target === lightbox) closeLb(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeLb(); });
    document.querySelectorAll('[data-lightbox]').forEach(function (img) {
      img.addEventListener('click', function () {
        lbImg.src = img.dataset.lightbox || img.src;
        lightbox.classList.add('is-open');
      });
    });
  }

  /* ---------- файл в форме ---------- */
  document.querySelectorAll('.form-file').forEach(function (wrap) {
    var input = wrap.querySelector('input[type=file]');
    var label = wrap.querySelector('.form-file__name');
    input.addEventListener('change', function () {
      if (input.files.length) label.textContent = input.files[0].name;
    });
  });

  /* ---------- отправка формы ---------- */
  document.querySelectorAll('[data-form]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var msg = form.querySelector('.form-msg');
      var fields = {
        name: form.querySelector('input[name=name]'),
        phone: form.querySelector('input[name=phone]'),
        email: form.querySelector('input[name=email]'),
        task: form.querySelector('input[name=task]'),
        comment: form.querySelector('textarea[name=comment]'),
        consent: form.querySelector('input[name=consent]')
      };
      var file = form.querySelector('input[name=file]');
      var ok = true;
      var setError = function (f, text) {
        if (!f) return;
        f.style.borderColor = '#ff8a8a';
        if (text && msg) { msg.textContent = text; msg.className = 'form-msg is-error'; }
        f.addEventListener('input', function () { f.style.borderColor = ''; }, { once: true });
      };
      if (!fields.name.value.trim() || fields.name.value.trim().length < 2) { setError(fields.name, 'Введите корректное имя.'); ok = false; }
      if (!fields.phone.value.trim() || !fields.phone.value.replace(/\D/g, '').match(/\d{6,}/)) { setError(fields.phone, 'Введите корректный телефон.'); ok = false; }
      if (fields.email.value && !fields.email.value.match(/^[^@\s]+@[^@\s]+\.[^@\s]+$/)) { setError(fields.email, 'Введите корректный e-mail.'); ok = false; }
      if (!fields.consent || !fields.consent.checked) {
        setError(fields.consent, 'Необходимо согласие на обработку персональных данных.');
        ok = false;
      }
      if (file && file.files.length && file.files[0].size > 25 * 1024 * 1024) { setError(file, 'Файл больше 25 МБ.'); ok = false; }
      if (!ok) return;

      var btn = form.querySelector('button[type=submit]');
      var btnText = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Отправка…';

      var fd = new FormData();
      fd.append('name', fields.name.value.trim());
      fd.append('phone', fields.phone.value.trim());
      fd.append('email', fields.email.value.trim());
      fd.append('task', fields.task.value.trim());
      if (fields.comment) fd.append('comment', fields.comment.value.trim());
      if (file && file.files.length) fd.append('file', file.files[0]);

      fetch('/api/lead', { method: 'POST', body: fd })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (res.ok) {
            msg.textContent = 'Спасибо! Заявка отправлена. Мы свяжемся с вами в ближайшее время.';
            msg.className = 'form-msg is-ok';
            form.reset();
            if (label) label.textContent = 'Файл не выбран';
          } else {
            msg.textContent = (res.d && res.d.error) || 'Ошибка отправки. Попробуйте ещё раз или позвоните нам.';
            msg.className = 'form-msg is-error';
          }
        })
        .catch(function () {
          msg.textContent = 'Ошибка сети. Попробуйте ещё раз или позвоните нам.';
          msg.className = 'form-msg is-error';
        })
        .finally(function () {
          btn.disabled = false;
          btn.textContent = btnText;
        });
    });
  });

  /* ---------- телефон: маска ---------- */
  document.querySelectorAll('input[type=tel]').forEach(function (t) {
    t.addEventListener('input', function () {
      var digits = t.value.replace(/\D/g, '');
      if (digits.length === 0) { t.value = ''; return; }
      var d = digits.slice(0, 11);
      var out = '+7';
      if (d.length > 1) out += ' (' + d.slice(1, 4);
      if (d.length >= 4) out += ') ' + d.slice(4, 7);
      if (d.length >= 7) out += '-' + d.slice(7, 9);
      if (d.length >= 9) out += '-' + d.slice(9, 11);
      t.value = out;
    });
  });
});