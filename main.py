# file: off_rest_example.py
import requests
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, 
                            QLineEdit, QTextEdit, QTabWidget, QVBoxLayout, 
                            QGroupBox,QMessageBox)

BASE = "https://world.openfoodfacts.org"

HEADERS = {
    "User-Agent": "Darcons-Trade-CalorieFetcher/1.0 (+https://darcons-trade.example)"
}

def get_product_by_barcode(barcode: str, fields=None, lang="ru", country="ru") -> dict:
    """
    Получение конкретного продукта по штрихкоду (API v2).
    """
    if fields is None:
        fields = "code,product_name,nutriments,brands,quantity,serving_size,language,lang,lc"
    url = f"{BASE}/api/v2/product/{barcode}"
    params = {"fields": fields, "lc": lang, "cc": country}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def search_products(query: str, page_size=100, fields=None, lang="ru", country="ru") -> dict:
    """
    Поиск продуктов по тексту (Search API v2).
    Пример фильтра: можно добавлять tags и условия по нутриентам.
    """
    if fields is None:
        fields = "code,product_name,brands,nutriments,quantity,serving_size,ecoscore_grade"
    url = f"{BASE}/cgi/search.pl"
    params = {
        "search_terms": query,
        "fields": fields,
        'json': 1,
        "page_size": page_size,
        "lc": lang,
        "cc": country,
    }

    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def extract_kcal(nutriments: dict) -> dict:
    """
    Извлекает калорийность и БЖУ.
    Возвращает значения на 100 г и на порцию (если доступно).
    """
    get = nutriments.get
    data = {
        "kcal_100g": get("energy-kcal_100g") or get("energy-kcal_value"),
        "protein_100g": get("proteins_100g"),
        "fat_100g": get("fat_100g"),
        "carbs_100g": get("carbohydrates_100g"),
        "kcal_serving": get("energy-kcal_serving"),
        "protein_serving": get("proteins_serving"),
        "fat_serving": get("fat_serving"),
        "carbs_serving": get("carbohydrates_serving"),
    }
    return {k: v for k, v in data.items() if v is not None}

# Настройка таблицы стилей для всего графического интерфейса пользователя
style_sheet = """
QWidget {
    background-color: white;
}

QWidget#Tabs {
    background-color: white;
    border-radius: 4px;
}

QLabel#Header {
    background-color: green;
    border-width: 2px;
    border-style: solid;
    border-radius: 4px;
    border-color: green;
    padding-left: 10px;
    color: white
}

QGroupBox {
    font-weight: bold;
    border: 2px solid green;
    border-radius: 5px;
    margin-top: 1ex;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
    background-color: green;
    color: white;
    border-radius: 3px;
}

QLineEdit {
    padding: 8px;
    border: 1px solid #CCC;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton {
    background-color: green;
    border: none;
    color: white;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    font-size: 14px;
    margin: 4px 2px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: lightgreen;
}

QPushButton:pressed {
    background-color: green;
}

QTextEdit {
    border: 1px solid #CCC;
    border-radius: 4px;
    padding: 8px;
    font-size: 14px;
    background-color: white;
}
"""

class Nutrition_window(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    
    def initializeUI(self):
        """Настройка графического интерфейса приложения."""
        self.setMinimumSize(800, 600)
        self.setWindowTitle("Поиск калорийности продуктов")
        self.setUpMainWindow()
        self.show()
    
    def setUpMainWindow(self):
        """Создание и расположение виджетов в главном окне."""
        # Создаем панель вкладок
        self.tab_bar = QTabWidget()
        
        # Создаем вкладки
        self.barcode_tab = QWidget()
        self.barcode_tab.setObjectName("Tabs")
        
        self.search_tab = QWidget()
        self.search_tab.setObjectName("Tabs")
        
        self.tab_bar.addTab(self.barcode_tab, "Поиск по штрихкоду")
        self.tab_bar.addTab(self.search_tab, "Поиск по названию")
        
        # Вызов методов для создания содержимого вкладок
        self.setupBarcodeTab()
        self.setupSearchTab()
        
        # Основной макет
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_bar)
        self.setLayout(main_layout)
    
    def setupBarcodeTab(self):
        """Настройка вкладки поиска по штрихкоду."""
        # Заголовок
        header_label = QLabel("ПОИСК ПРОДУКТА ПО ШТРИХКОДУ")
        header_label.setObjectName("Header")
        
        # Группа для ввода штрихкода
        barcode_group = QGroupBox("Введите штрихкод продукта")
        barcode_layout = QVBoxLayout()
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Например: 8445290140036")
        
        search_button = QPushButton("Найти продукт")
        search_button.clicked.connect(self.searchByBarcode)
        
        barcode_layout.addWidget(self.barcode_input)
        barcode_layout.addWidget(search_button)
        barcode_group.setLayout(barcode_layout)
        
        # Область для отображения результатов
        result_group = QGroupBox("Информация о продукте")
        result_layout = QVBoxLayout()
        
        self.barcode_result = QTextEdit()
        self.barcode_result.setReadOnly(True)
        
        result_layout.addWidget(self.barcode_result)
        result_group.setLayout(result_layout)
        
        # Основной макет вкладки
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(header_label)
        tab_layout.addWidget(barcode_group)
        tab_layout.addWidget(result_group)
        tab_layout.addStretch()
        
        self.barcode_tab.setLayout(tab_layout)
    
    def setupSearchTab(self):
        """Настройка вкладки поиска по названию."""
        # Заголовок
        header_label = QLabel("ПОИСК ПРОДУКТА ПО НАЗВАНИЮ")
        header_label.setObjectName("Header")
        
        # Группа для ввода названия
        search_group = QGroupBox("Введите название продукта")
        search_layout = QVBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Например: молоко")
        
        search_button = QPushButton("Найти продукты")
        search_button.clicked.connect(self.searchByName)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        search_group.setLayout(search_layout)
        
        # Область для отображения результатов
        result_group = QGroupBox("Результаты поиска")
        result_layout = QVBoxLayout()
        
        self.search_result = QTextEdit()
        self.search_result.setReadOnly(True)
        
        result_layout.addWidget(self.search_result)
        result_group.setLayout(result_layout)
        
        # Основной макет вкладки
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(header_label)
        tab_layout.addWidget(search_group)
        tab_layout.addWidget(result_group)
        tab_layout.addStretch()
        
        self.search_tab.setLayout(tab_layout)
    
    def searchByBarcode(self):
        """Поиск продукта по штрихкоду."""
        barcode = self.barcode_input.text().strip()
        
        if not barcode:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите штрихкод")
            return
        
        try:
            # Используем существующую функцию
            product_data = get_product_by_barcode(barcode)
                
            product = product_data["product"]
            self.displayProductInfo(product, self.barcode_result)

        except Exception as e:
            self.barcode_result.setText("Продукт не найден. Проверьте правильность штрихкода.")

    def searchByName(self):
        """Поиск продуктов по названию."""
        query = self.search_input.text().strip()
        
        if not query:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите название продукта")
            return

        # Используем существующую функцию
        search_data = search_products(query)
            
        products = search_data.get("products", [])
            
        if products:
            result_text = "\n" + "="*50 + "\n\n"
                
            for i, product in enumerate(products, 1):
                result_text += f"Продукт {i}\n"
                result_text += self.formatProductInfo(product)
                result_text += "\n" + "="*50 + "\n\n"
                
            self.search_result.setText(result_text)
        else:
            self.search_result.setText("Продукты не найдены. Попробуйте изменить запрос.")
    
    def formatProductInfo(self, product):
        """Форматирование информации о продукте для отображения."""
        info = f"Название: {product.get('product_name', 'Не указано')}\n"
        info += f"Бренд: {product.get('brands', 'Не указан')}\n"
        info += f"Штрихкод: {product.get('code', 'Не указан')}\n"
        info += f"Количество: {product.get('quantity', 'Не указано')}\n"
        info += f"Размер порции: {product.get('serving_size', 'Не указан')}\n"
        
        # Информация о питательной ценности
        nutriments = product.get('nutriments', {})
        nutrition_info = extract_kcal(nutriments)
        
        if nutrition_info:
            info += "\nПищевая ценность\n"
            if 'kcal_100g' in nutrition_info:
                info += f"Калории на 100г: {nutrition_info['kcal_100g']} ккал\n"
            if 'protein_100g' in nutrition_info:
                info += f"Белки на 100г: {nutrition_info['protein_100g']} г\n"
            if 'fat_100g' in nutrition_info:
                info += f"Жиры на 100г: {nutrition_info['fat_100g']} г\n"
            if 'carbs_100g' in nutrition_info:
                info += f"Углеводы на 100г: {nutrition_info['carbs_100g']} г\n"
            
            # Информация на порцию
            if any(key.endswith('_serving') for key in nutrition_info):
                info += "\nНа порцию\n"
                if 'kcal_serving' in nutrition_info:
                    info += f"Калории: {nutrition_info['kcal_serving']} ккал\n"
                if 'protein_serving' in nutrition_info:
                    info += f"Белки: {nutrition_info['protein_serving']} г\n"
                if 'fat_serving' in nutrition_info:
                    info += f"Жиры: {nutrition_info['fat_serving']} г\n"
                if 'carbs_serving' in nutrition_info:
                    info += f"Углеводы: {nutrition_info['carbs_serving']} г\n"
        else:
            info += "\nИнформация о пищевой ценности недоступна\n"
        
        return info
    
    def displayProductInfo(self, product, text_widget):
        """Отображение информации о продукте в текстовом виджете."""
        formatted_info = self.formatProductInfo(product)
        text_widget.setText(formatted_info)

if __name__ == "__main__":
    '''
    # Пример 1: по штрихкоду
    barcode = "5449000000996"  # Coca-Cola 0.33 л (пример; замените своим)
    prod = get_product_by_barcode(barcode)
    if prod.get("product"):
        p = prod["product"]
        print("Название:", p.get("product_name"))
        print("Бренд:", p.get("brands"))
        print("Упаковка:", p.get("quantity"))
        print("Порция:", p.get("serving_size"))
        print("Нутриенты:", extract_kcal(p.get("nutriments", {})))
    else:
        print("Продукт не найден")

    # Пример 2: поиск по названию
    res = search_products("молоко")
    for i, p in enumerate(res.get("products", []), 1):
        print(f"\nРезультат {i}:")
        print("Штрихкод:", p.get("code"))
        print("Название:", p.get("product_name"))
        print("Бренд:", p.get("brands"))
        print("Нутриенты:", extract_kcal(p.get("nutriments", {})))
    '''
    app = QApplication(sys.argv)
    app.setStyleSheet(style_sheet)
    window = Nutrition_window()
    sys.exit(app.exec())