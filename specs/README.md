# SignalForge specifications

Каталог `specs/` содержит утверждаемые требования и технические решения SignalForge.

Рабочие заметки и исходные вводные из `docs/project-context/` сохраняют контекст, но не являются источником утверждённых требований.

## Structure

```text
specs/
  product/       Product specification
  features/      Feature specifications, designs, tasks and decisions
  architecture/  Устойчивые общесистемные решения
  templates/     Шаблоны SDD-документов
```

Каждая feature размещается в отдельном нумерованном каталоге:

```text
specs/features/001-feature-name/
  spec.md
  design.md
  tasks.md
  decisions.md
```

## Source of truth

- Product specification определяет цели, пользователей и границы продукта.
- Feature specification определяет требуемое наблюдаемое поведение.
- Technical design описывает способ реализации утверждённой feature specification.
- Tasks декомпозируют утверждённые требования и design на проверяемые шаги.
- Decisions фиксируют значимые решения, альтернативы и последствия.
- Architecture содержит решения, действующие сразу для нескольких features.

При противоречии реализация должна быть остановлена до уточнения спецификации. Код не может вводить поведение, отсутствующее в утверждённой feature specification.

## Specification lifecycle

Используются следующие статусы:

```text
Draft → In Review → Approved → Implemented → Verified
```

- `Draft` — документ создаётся или существенно изменяется.
- `In Review` — документ подготовлен для проверки, но ещё не разрешает реализацию.
- `Approved` — требования явно утверждены человеком и разрешают следующий этап SDD.
- `Implemented` — все запланированные задачи реализации завершены, но итоговая проверка feature ещё не подтверждена.
- `Verified` — реализация успешно проверена против всей утверждённой спецификации.

Codex не имеет права самостоятельно присваивать статус `Approved`. Существенное изменение scope, requirement, constraint или acceptance criterion возвращает документ в `Draft` и требует повторного review и человеческого утверждения.

## Required workflow

1. Product specification.
2. Feature specification со статусом `Draft`.
3. Specification review.
4. Явное утверждение человеком.
5. Technical design.
6. Task decomposition.
7. Реализация одной выбранной задачи.
8. Проверка задачи и обновление её статуса.
9. Проверка всей feature против specification.
10. Code review и обновление статуса документов.

Codex не переходит к следующей задаче или стадии автоматически.
