# Viktor Workflow Portable — clean core

Окремий компактний пакет загальних правил аналізу/архітектури, порожніх BA/experience/recovery templates та 12 оригінальних synthetic діаграм (25 offline exports і 8 optional native reference files). Це **не повна приватна конфігурація власника**. Не містить персонального профілю, чужих акаунтів/прав, private URLs, project logs, Git history, credentials або сторонніх engines/source snapshots.

## Власна установка

1. Отримайте clean ZIP, manifest і SHA256 через погоджений канал; цей clean пакет поширюється окремо від приватних резервних копій. Звірте trusted SHA256 до розпакування та перевірте ZIP paths/types/CRC у новому каталозі. Не запускайте archived code до перевірки джерела.
2. Прочитайте LICENSE/PROVENANCE. Усі вкладені матеріали оригінальні й MIT; upstream engines не вкладені й мають власні умови. `references/diagrams/sources.json` містить лише primary upstream metadata/pins і межі перевірки, не дозвіл автоматичного виконання.
3. Для cloud завантажте ZIP через підтримуваний Plugin Creator у **своєму** акаунті й створіть власний приватний plugin. Для Codex standalone установіть `skills/workflow-portable` у підтримуваний каталог skills після порівняння/backup наявного однойменного skill. Особисті preferences задайте самостійно; доступ автора не переноситься.
4. Для локальних перевірок потрібен Python 3.10+, standard library. З кореня розпакованого пакета:

   ```text
   python3 -I -S verify_package.py .
   python3 -I -S skills/workflow-portable/scripts/diagram_library.py check
   python3 -I -S skills/workflow-portable/scripts/diagram_library.py lookup bpmn --limit 2
   ```

5. Новий сеанс має фактично бачити `workflow-portable`. Попросіть проаналізувати вигадану BA-задачу, прочитавши тільки analysis template і одну релевантну diagram entry. Не підключайте чужі credentials/сервіси. Rollback standalone установки — прибрати лише цю нову навичку та відновити свою збережену попередню копію; cloud — власний штатний механізм, без видалення чужих плагінів.

Original offline exports перевірені; native PlantUML/Mermaid/D2/Structurizr/Diagrams engines тут не запускались. Для native rendering потрібні окремі перевірені dependencies (наприклад Java/Graphviz або Node залежно від engine/version); жодний installer не запускається пакетом. BPMN exports не є execution engine або повною XSD сертифікацією. Не надсилайте private models зовнішнім renderers без авторизації.

Сканер перевіряє конкретні відомі private markers, inventory, hashes і локальні links; це не доказ відсутності всіх можливих секретів/malware. Ізольовані tests не є фізичною перевіркою іншого комп'ютера або cloud discovery іншого акаунта. Розклад/update runner не створено.
