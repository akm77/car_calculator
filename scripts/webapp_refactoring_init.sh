#!/bin/bash
# WebApp Refactoring - Этап 0: Подготовка
# Запустите этот скрипт для создания структуры папок

set -e

echo "🚀 WebApp Refactoring - Подготовка"
echo "===================================="
echo ""

# Текущая директория
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEBAPP_DIR="$PROJECT_ROOT/app/webapp"

cd "$PROJECT_ROOT"

# 1. Создать структуру папок
echo "📁 Создание структуры папок..."

mkdir -p "$WEBAPP_DIR/css"
mkdir -p "$WEBAPP_DIR/js/config"
mkdir -p "$WEBAPP_DIR/js/utils"
mkdir -p "$WEBAPP_DIR/js/modules"

echo "   ✅ app/webapp/css/"
echo "   ✅ app/webapp/js/config/"
echo "   ✅ app/webapp/js/utils/"
echo "   ✅ app/webapp/js/modules/"
echo ""

# 2. Создать бэкап
echo "💾 Создание бэкапа index.html..."

if [ -f "$WEBAPP_DIR/index.html" ]; then
    cp "$WEBAPP_DIR/index.html" "$WEBAPP_DIR/index.html.backup"
    echo "   ✅ Создан: app/webapp/index.html.backup"
else
    echo "   ⚠️  Файл index.html не найден"
fi
echo ""

# 3. Создать .gitkeep для пустых папок
echo "📝 Создание .gitkeep файлов..."

touch "$WEBAPP_DIR/css/.gitkeep"
touch "$WEBAPP_DIR/js/config/.gitkeep"
touch "$WEBAPP_DIR/js/utils/.gitkeep"
touch "$WEBAPP_DIR/js/modules/.gitkeep"

echo "   ✅ .gitkeep файлы созданы"
echo ""

# 4. Вывести структуру
echo "📂 Текущая структура:"
echo ""

if command -v tree &> /dev/null; then
    tree -L 3 "$WEBAPP_DIR" -I '__pycache__|*.pyc'
else
    find "$WEBAPP_DIR" -type d -maxdepth 3 | sed "s|$WEBAPP_DIR|app/webapp|" | sort
fi

echo ""
echo "✨ Подготовка завершена!"
echo ""
echo "📚 Следующие шаги:"
echo "   1. Прочитать: docs/webapp_refactoring_plan.md (Этап 1)"
echo "   2. Начать с вынесения CSS в отдельные файлы"
echo "   3. После каждого этапа - тестировать и коммитить"
echo ""
echo "💡 Быстрый старт:"
echo "   cd $PROJECT_ROOT"
echo "   # Открыть план:"
echo "   cat docs/webapp_refactoring_plan.md"
echo ""

