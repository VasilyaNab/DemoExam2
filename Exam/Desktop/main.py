from django.db.models import Q
from django.core.files import File

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFrame, QDialog, QFileDialog, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import QDate

from .models import *

from .pages.MainWindow import Ui_MainWindow
from .pages.Product import Ui_Product
from .pages.ProductsWindow import Ui_ProductsWindow

import os

class MainWindow(QMainWindow):
    # Главное окно с авторизацией
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))

        # Подключаем кнопки к функциям
        self.ui.Enter.clicked.connect(self.login)
        self.ui.Guest.clicked.connect(self.open_products)

    def login(self):
        # Проверка логина и пароля пользователя
        login = self.ui.Login.text()
        password = self.ui.Password.text()

        # Ищем пользователя в БД
        user = User.objects.filter(login=login, password=password).first()
        if user:
            self.open_products(user)  # Вход выполнен
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные данные")

    def open_products(self, user=None):
        # Открываем окно с товарами
        self.window = ProductsWindow(user)
        self.window.show()
        self.close()  # Закрываем окно авторизации

class ProductFrame(QFrame):
    # Карточка товара - отображается в списке
    def __init__(self, product, parents):
        super(ProductFrame, self).__init__()
        self.ui = Ui_Product()
        ui = self.ui
        ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.product = product
        self.parents = parents  # Ссылка на родительское окно

        # Заполняем информацию о товаре
        category = product.category.name if product.category else ""
        ui.Type.setText(f"{category} | {product.name}")
        ui.Description.setText(ui.Description.text() + product.description)
        ui.Supplier.setText(ui.Supplier.text() + product.supplier)
        ui.Seller.setText(ui.Seller.text() + product.seller)
        ui.Count.setText(ui.Count.text() + str(product.count))

        # Настройка цены и скидки
        ui.Discount.setText(str(product.discount) + ui.Discount.text())
        if product.discount > 0:
            ui.OldPrice.setText(str(product.price))  # Показываем старую цену
        else:
            ui.OldPrice.hide()  # Скрываем, если скидки нет

        # Рассчитываем новую цену со скидкой
        new_price = int(product.price * (1 - product.discount / 100))
        ui.NewPrice.setText(str(new_price))

        # Меняем цвет скидки в зависимости от размера
        if product.discount > 15:
            ui.Discount.setStyleSheet("background-color:#2E8B57")  # Зеленый для большой скидки
        else:
            ui.Discount.setStyleSheet("background-color:red")  # Красный для маленькой

        # Если товара нет на складе - серый текст
        if product.count <= 0:
            ui.Count.setStyleSheet("color:#aaa")

        # Загружаем картинку товара
        pixmap = QPixmap("picture.png")  # Картинка по умолчанию
        if product.image:
            path = product.image.name
            if os.path.exists(path):
                pixmap = QPixmap(path)
        ui.Image.setPixmap(pixmap)
        ui.Image.setScaledContents(True)
        
        # Подключаем кнопки управления товаром
        ui.Update.clicked.connect(self.update_product)
        ui.Delete.clicked.connect(self.delete_product)

    def delete_product(self):
        # Удаление товара из БД
        if QMessageBox.question(self, "Удаление", "Удалить?") == QMessageBox.Yes:
            # Удаляем файл с картинкой, если есть
            if self.product.image:
                self.product.image.delete()
            self.product.delete()
        self.parents.load_products()  # Обновляем список

    def update_product(self):
        # Редактирование товара (пока не реализовано)
        pass

class ProductsWindow(QMainWindow):
    # Окно со списком товаров и фильтрами
    def __init__(self, user=None):
        super().__init__()
        self.ui = Ui_ProductsWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.user = user

        # Отображаем имя пользователя
        if user:
            self.ui.FIO.setText(str(user))
        else:
            self.ui.FIO.setText("Гость")

        # Заполняем выпадающий список категорий
        self.ui.comboBoxFilter.addItem("Все категории")
        for cat in Category.objects.all():
            self.ui.comboBoxFilter.addItem(cat.name)

        # Варианты сортировки
        self.ui.comboBoxSort.addItems([
            "Без сортировки",
            "По возрастанию цены",
            "По убыванию цены"
        ])

        # Подключаем фильтры и поиск
        self.ui.Search.textChanged.connect(self.load_products)  # Поиск при вводе
        self.ui.comboBoxSort.currentIndexChanged.connect(self.load_products)  # Сортировка
        self.ui.comboBoxFilter.currentIndexChanged.connect(self.load_products)  # Фильтр по категории
        self.ui.Exit.clicked.connect(self.exit)  # Выход

        self.load_products()  # Загружаем товары

    def load_products(self):
        # Загрузка и отображение товаров с учетом фильтров
        ui = self.ui
        # Очищаем старые карточки товаров
        layout = ui.scrollAreaWidgetContents.layout()
        if layout is None:
            layout = QVBoxLayout(ui.scrollAreaWidgetContents)
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # Базовый запрос всех товаров
        products = Product.objects.all()
        # Фильтр по поисковому запросу
        search = ui.Search.text()
        if search:
            products = products.filter(name__icontains=search)
        # Фильтр по категории
        category = ui.comboBoxFilter.currentText()
        if category != "Все категории":
            products = products.filter(category__name=category)
        # Сортировка
        sort = ui.comboBoxSort.currentIndex()
        if sort == 1:
            products = products.order_by("price")  # По возрастанию
        elif sort == 2:
            products = products.order_by("-price")  # По убыванию
        # Создаем и добавляем карточки товаров
        for p in products:
            frame = ProductFrame(p, self)
            ui.scrollAreaWidgetContents.layout().addWidget(frame)

    def exit(self):
        # Выход в главное окно
        self.window = MainWindow()
        self.window.show()
        self.close()