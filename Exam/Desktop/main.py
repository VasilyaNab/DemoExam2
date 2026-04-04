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
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))

        self.ui.Enter.clicked.connect(self.login)
        self.ui.Guest.clicked.connect(self.open_products)

    def login(self):
        login = self.ui.Login.text()
        password = self.ui.Password.text()

        user = User.objects.filter(login=login, password=password).first()

        if user:
            self.open_products(user)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные данные")

    def open_products(self, user=None):
        self.window = ProductsWindow(user)
        self.window.show()
        self.close()

class ProductFrame(QFrame):
    def __init__(self, product, parents):
        super(ProductFrame, self).__init__()

        self.ui = Ui_Product()
        ui = self.ui

        ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.product = product
        self.parents = parents

        category = product.category.name if product.category else ""
        ui.Type.setText(f"{category} | {product.name}")
        ui.Description.setText(ui.Description.text() + product.description)
        ui.Supplier.setText(ui.Supplier.text() + product.supplier)
        ui.Seller.setText(ui.Seller.text() + product.seller)
        ui.Count.setText(ui.Count.text() + str(product.count))

        # скидка и цена
        ui.Discount.setText(str(product.discount) + ui.Discount.text())

        if product.discount > 0:
            ui.OldPrice.setText(str(product.price))
        else:
            ui.OldPrice.hide()

        new_price = int(product.price * (1 - product.discount / 100))
        ui.NewPrice.setText(str(new_price))

        # цвет скидки
        if product.discount > 15:
            ui.Discount.setStyleSheet("background-color:#2E8B57")
        else:
            ui.Discount.setStyleSheet("background-color:red")

        # если нет на складе
        if product.count <= 0:
            ui.Count.setStyleSheet("color:#aaa")

        # картинка
        pixmap = QPixmap("picture.png")

        if product.image:
            path = product.image.name
            if os.path.exists(path):
                pixmap = QPixmap(path)

        ui.Image.setPixmap(pixmap)
        ui.Image.setScaledContents(True)
        # кнопки (если есть)
        ui.Update.clicked.connect(self.update_product)
        ui.Delete.clicked.connect(self.delete_product)

    def delete_product(self):
        if QMessageBox.question(self, "Удаление", "Удалить?") == QMessageBox.Yes:
            if self.product.image:
                self.product.image.delete()
            self.product.delete()
        self.parents.load_products()

    def update_product(self):
        pass  # если не нужен — оставь так
class ProductsWindow(QMainWindow):
    def __init__(self, user=None):
        super().__init__()

        self.ui = Ui_ProductsWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.user = user

        # ФИО
        if user:
            self.ui.FIO.setText(str(user))
        else:
            self.ui.FIO.setText("Гость")

        # фильтр (по категориям)
        self.ui.comboBoxFilter.addItem("Все категории")
        for cat in Category.objects.all():
            self.ui.comboBoxFilter.addItem(cat.name)

        # сортировка
        self.ui.comboBoxSort.addItems([
            "Без сортировки",
            "По возрастанию цены",
            "По убыванию цены"
        ])

        # сигналы
        self.ui.Search.textChanged.connect(self.load_products)
        self.ui.comboBoxSort.currentIndexChanged.connect(self.load_products)
        self.ui.comboBoxFilter.currentIndexChanged.connect(self.load_products)

        self.ui.Exit.clicked.connect(self.exit)

        self.load_products()

    def load_products(self):
        ui = self.ui

        # очистка
        layout = ui.scrollAreaWidgetContents.layout()
        if layout is None:
            layout = QVBoxLayout(ui.scrollAreaWidgetContents)

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        products = Product.objects.all()

        # поиск
        search = ui.Search.text()
        if search:
            products = products.filter(name__icontains=search)

        # фильтр
        category = ui.comboBoxFilter.currentText()
        if category != "Все категории":
            products = products.filter(category__name=category)

        # сортировка
        sort = ui.comboBoxSort.currentIndex()

        if sort == 1:
            products = products.order_by("price")
        elif sort == 2:
            products = products.order_by("-price")

        # вывод
        for p in products:
            frame = ProductFrame(p, self)
            ui.scrollAreaWidgetContents.layout().addWidget(frame)

    def exit(self):
        self.window = MainWindow()
        self.window.show()
        self.close()