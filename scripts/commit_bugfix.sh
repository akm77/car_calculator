#!/bin/bash
# Скрипт для коммита исправления бага engine_power_hp

echo "🐛 Bug Fix: engine_power_hp в shareResult()"
echo "============================================"
echo ""

# Показываем измененные файлы
echo "📝 Измененные файлы:"
git status --short

echo ""
echo "✅ Запускаем тесты..."
python tests/manual/test_share_result_bugfix.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Все тесты пройдены!"
    echo ""
    echo "📦 Готов к коммиту. Выполните:"
    echo ""
    echo "  git add app/webapp/index.html CHANGELOG.md"
    echo "  git add tests/manual/test_share_result_bugfix.py"
    echo "  git add docs/BUG_FIX_REPORT.md docs/BUGFIX_SUMMARY.md docs/GIT_COMMIT_MESSAGE.txt"
    echo "  git commit -F docs/GIT_COMMIT_MESSAGE.txt"
    echo "  git push origin main"
    echo ""
else
    echo ""
    echo "❌ Тесты не пройдены! Исправьте ошибки перед коммитом."
    exit 1
fi

