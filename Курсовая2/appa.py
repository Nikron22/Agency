from flask import render_template, request
import traceback
from sqlalchemy import text


@app.route('/properties')
def view_properties():
    """
    Отображение списка объектов недвижимости с фильтрацией
    """
    try:
        print("=" * 80)
        print("DEBUG: Начало выполнения view_properties()")
        print("=" * 80)

        # ==================== 1. ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД ====================
        print("\n1. Проверка подключения к базе данных...")
        try:
            # Проверяем, можем ли выполнить простой запрос
            test_result = db.session.execute(text("SELECT 1")).scalar()
            print(f"   ✓ Подключение к БД работает: {test_result}")
        except Exception as e:
            print(f"   ✗ Ошибка подключения к БД: {e}")
            return render_template('properties/list.html',
                                   properties=[],
                                   property_types=[],
                                   regions=[],
                                   rooms_options=[],
                                   filters={},
                                   error=f"Ошибка БД: {e}")

        # ==================== 2. ПРОВЕРКА СУЩЕСТВОВАНИЯ ТАБЛИЦЫ ====================
        print("\n2. Проверка существования таблицы properties...")
        try:
            # Проверяем, существует ли таблица
            table_check = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'properties'
                )
            """)).scalar()

            if table_check:
                print("   ✓ Таблица 'properties' существует")
            else:
                print("   ✗ Таблица 'properties' НЕ существует!")
                return render_template('properties/list.html',
                                       properties=[],
                                       property_types=[],
                                       regions=[],
                                       rooms_options=[],
                                       filters={},
                                       error="Таблица 'properties' не найдена")
        except Exception as e:
            print(f"   ✗ Ошибка проверки таблицы: {e}")

        # ==================== 3. ПРОВЕРКА КОЛИЧЕСТВА ЗАПИСЕЙ ====================
        print("\n3. Проверка количества записей в таблице...")
        try:
            count_result = db.session.execute(text("SELECT COUNT(*) FROM properties")).scalar()
            print(f"   ✓ Всего записей в таблице properties: {count_result}")
        except Exception as e:
            print(f"   ✗ Ошибка при подсчете записей: {e}")
            count_result = 0

        # ==================== 4. ПОЛУЧЕНИЕ ДАННЫХ ====================
        print("\n4. Получение данных из таблицы...")
        properties = []

        if count_result > 0:
            try:
                # Вариант 1: Если используете SQLAlchemy модели
                # from models import Property
                # properties = Property.query.all()

                # Вариант 2: Сырой SQL запрос (универсальный)
                sql_query = text("SELECT * FROM properties LIMIT 10")
                result = db.session.execute(sql_query)

                # Получаем все записи
                rows = result.fetchall()

                # Преобразуем в список словарей для удобства
                properties = []
                for row in rows:
                    # row - это Row объект, преобразуем в словарь
                    row_dict = dict(row._mapping)
                    properties.append(row_dict)

                print(f"   ✓ Получено объектов: {len(properties)}")

                # Выводим первые 3 записи для отладки
                print("\n   Первые 3 объекта:")
                for i, prop in enumerate(properties[:3]):
                    print(f"   Объект {i + 1}:")
                    for key, value in prop.items():
                        print(f"     {key}: {value}")
                    print()

            except Exception as e:
                print(f"   ✗ Ошибка при получении данных: {e}")
                print(f"   Traceback: {traceback.format_exc()}")
        else:
            print("   ⚠ Таблица пуста, нет данных для отображения")

        # ==================== 5. ПОЛУЧЕНИЕ ФИЛЬТРОВ ИЗ URL ====================
        print("\n5. Парсинг фильтров из URL...")
        filters = {
            'type': request.args.get('type', ''),
            'region': request.args.get('region', ''),
            'rooms': request.args.get('rooms', ''),
            'available': request.args.get('available', ''),
            'min_price': request.args.get('min_price', ''),
            'max_price': request.args.get('max_price', ''),
            'min_area': request.args.get('min_area', ''),
            'max_area': request.args.get('max_area', ''),
            'address': request.args.get('address', '')
        }

        print(f"   Полученные фильтры: {filters}")

        # ==================== 6. ПРИМЕНЕНИЕ ФИЛЬТРОВ ====================
        print("\n6. Применение фильтров к данным...")
        filtered_properties = []

        if properties:
            for prop in properties:
                include = True

                # Фильтр по типу
                if filters['type'] and prop.get('type') != filters['type']:
                    include = False

                # Фильтр по району
                if include and filters['region'] and prop.get('region') != filters['region']:
                    include = False

                # Фильтр по количеству комнат
                if include and filters['rooms']:
                    try:
                        if str(prop.get('rooms', '')) != filters['rooms']:
                            include = False
                    except:
                        pass

                # Фильтр по статусу
                if include and filters['available']:
                    is_available = filters['available'] == 'available'
                    prop_available = prop.get('available', False)
                    if prop_available != is_available:
                        include = False

                if include:
                    filtered_properties.append(prop)

            print(f"   После фильтрации осталось: {len(filtered_properties)} объектов")

        # ==================== 7. ПОДГОТОВКА ДАННЫХ ДЛЯ ФИЛЬТРОВ ====================
        print("\n7. Подготовка данных для выпадающих списков...")

        # Получаем уникальные значения для фильтров
        try:
            if properties:
                # Типы недвижимости
                property_types = sorted(set([p.get('type', '') for p in properties if p.get('type')]))
                print(f"   Найдены типы: {property_types}")

                # Районы
                regions = sorted(set([p.get('region', '') for p in properties if p.get('region')]))
                print(f"   Найдены районы: {regions}")

                # Количество комнат
                rooms_set = sorted(set([p.get('rooms', 0) for p in properties if p.get('rooms') is not None]))
                print(f"   Найдены комнаты: {rooms_set}")
            else:
                property_types = ['Квартира', 'Дом', 'Коммерция', 'Участок']
                regions = ['Центр', 'Север', 'Юг', 'Запад', 'Восток']
                rooms_set = [1, 2, 3, 4, 5]
                print("   Используются значения по умолчанию")

        except Exception as e:
            print(f"   ✗ Ошибка при подготовке фильтров: {e}")
            property_types = []
            regions = []
            rooms_set = []

        # ==================== 8. РЕНДЕРИНГ ШАБЛОНА ====================
        print("\n8. Рендеринг шаблона...")
        print(f"   Передаем в шаблон:")
        print(f"   - properties: {len(filtered_properties)} объектов")
        print(f"   - property_types: {len(property_types)} вариантов")
        print(f"   - regions: {len(regions)} районов")
        print(f"   - rooms_options: {len(rooms_set)} вариантов")

        return render_template('properties/list.html',
                               properties=filtered_properties,
                               property_types=property_types,
                               regions=regions,
                               rooms_options=rooms_set,
                               filters=filters)

    except Exception as e:
        print("\n" + "!" * 80)
        print("КРИТИЧЕСКАЯ ОШИБКА В view_properties():")
        print(str(e))
        print(traceback.format_exc())
        print("!" * 80)

        return render_template('properties/list.html',
                               properties=[],
                               property_types=[],
                               regions=[],
                               rooms_options=[],
                               filters={},
                               error=f"Ошибка: {str(e)}")