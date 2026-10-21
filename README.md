# Viktor Workflow Portable 0.1.0

Очищений загальний пакет для власного акаунта: аналіз і delivery workflow, порожні BA/experience/recovery templates та оригінальні synthetic діаграми. **Це компактний portable core, а не повна приватна конфігурація автора.**

## Завантажити

- [ZIP 0.1.0 — пряме скачування](https://raw.githubusercontent.com/vipotestatem777/new/master/viktor-workflow-portable/releases/v0.1.0/viktor-workflow-portable-0.1.0.zip)
- [SHA256SUMS](viktor-workflow-portable/releases/v0.1.0/SHA256SUMS.txt)
- [Вихідні файли й інструкція встановлення](viktor-workflow-portable/source/README.md)
- [Ліцензія MIT](LICENSE), [походження та межі перевірки](viktor-workflow-portable/source/PROVENANCE.json)

ZIP: **74010 bytes**, **60 файлів**. SHA256: `a5d34b4317b643f9f06edce80084dbd8f5ee008c4e675e97dcc7f9ffd87e3a04`.

## Склад і власна установка

Загальна навичка workflow-portable, BA analysis template, порожні lesson/index templates, recovery policy; 12 оригінальних редагованих моделей, 25 offline exports (SVG/draw.io/BPMN) та 8 optional native reference examples. Python 3.10+ standard library потрібен лише для локальних перевірок/export CLI; external engines не вкладені. Під власним акаунтом імпортуйте ZIP через підтримуваний Plugin Creator або встановіть skills/workflow-portable у підтримуваний local skills directory після backup/порівняння наявної копії. Відкрийте новий сеанс і перевірте фактично loaded path. Подробиці — README усередині ZIP.

У пакет не включені особисті інструкції/профіль, приватні проєкти/журнали/URLs, credentials, Git history або upstream engines/source snapshots. Кожен одержувач використовує власні доступи. Приватні резервні копії залишаються приватними. Діаграми використовуються лише за запитом або реальною потребою; приватні моделі не відправляються зовнішнім renderers автоматично.

## Перевірки та обмеження

Перевірені inventory, SHA256, licenses/provenance вибраних оригінальних матеріалів, privacy markers (включно з самим verifier), links, 7 mutation tests і 12 models / 25 exports. Тести: `python3 -B -I -S -m unittest discover -s tests`. Немає обіцянки абсолютної безпеки, native engine roundtrip, повної BPMN XSD сертифікації або фізичного тесту іншого комп'ютера/іншого cloud акаунта. Автоматичного updater, installers, CI runner чи нових платних ресурсів немає.

Сторонні tools мають власні licenses/залежності/ліміти; включена MIT ліцензія не перелiцензовує upstream. Перед їх застосуванням звіряйте pin, версію, документацію, ліцензію та потрібні мережеві/секретні дії.
