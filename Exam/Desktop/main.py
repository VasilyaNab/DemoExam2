from django.db.models import Q
from django.core.files import File

from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QFrame, QDialog,
    QFileDialog, QVBoxLayout
)
from PySide6.QtGui import QPixmap, QIcon

from .models import *
from .pages.MainWindow import Ui_MainWindow
from .pages.Product import Ui_Product
from .pages.ProductsWindow import Ui_ProductsWindow
from .pages.ProductDialog import Ui_ProductDialog

import os


# ===================== Роли =====================
class Role:
    ADMIN = ("Администратор",)
    MANAGER = ("Администратор", "Менеджер")

    @staticmethod
    def check_lvl(user):
        if user:
            if user.role in Role.ADMIN:
                return 2
            elif user.role in Role.MANAGER:
                return 1
        return 0


# ===================== Главное окно =====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        ui = self.ui

        ui.Login.setText("starka78@mail.ru")
        ui.Password.setText("9SdkLp012")

        ui.Enter.clicked.connect(self.login)
        ui.Guest.clicked.connect(self.open_products)

    def login(self):
        ui = self.ui

        user = User.objects.filter(
            login=ui.Login.text(),
            password=ui.Password.text()
        ).first()

        if not user:
            QMessageBox.warning(self, "Ошибка", "Такого пользователя не существует")
            return

        self.open_products(user)

    def open_products(self, user=None):
        self.window = ProductsWindow(user)
        self.window.show()
        self.close()


# ===================== Карточка товара =====================
class ProductFrame(QFrame):
    def __init__(self, product: Product, parents):
        super().__init__()
        self.ui = Ui_Product()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))

        ui = self.ui
        p = product

        self.product = p
        self.parents = parents

        # Текст
        category = p.category.name if p.category else ""
        ui.Type.setText(f"{category} | {p.name}")
        ui.Description.setText(ui.Description.text() + p.description)
        ui.Supplier.setText(ui.Supplier.text() + p.supplier)
        ui.Seller.setText(ui.Seller.text() + p.seller)
        ui.Count.setText(ui.Count.text() + str(p.count))

        # Цена
        ui.Discount.setText(f"{p.discount}{ui.Discount.text()}")
        ui.NewPrice.setText(str(int(p.price * (1 - p.discount / 100))))

        if p.discount > 0:
            ui.OldPrice.setText(str(p.price))
        else:
            ui.OldPrice.hide()

        ui.Discount.setStyleSheet(
            "background-color:#2E8B57" if p.discount > 15 else "background-color:red"
        )

        if p.count <= 0:
            ui.Count.setStyleSheet("color:#aaa")

        # Картинка
        pixmap = QPixmap(p.image.path) if p.image and os.path.exists(p.image.path) else QPixmap("picture.png")
        ui.Image.setPixmap(pixmap)
        ui.Image.setScaledContents(True)

        # Кнопки
        ui.Update.clicked.connect(self.update_product)
        ui.Delete.clicked.connect(self.delete_product)

        if Role.check_lvl(parents.user) < 2:
            ui.Update.hide()
            ui.Delete.hide()

    def delete_product(self):
        if QMessageBox.question(self, "Удаление", "Вы точно хотите удалить этот обьект?") == QMessageBox.Yes:
            if self.product.image:
                self.product.image.delete()
            self.product.delete()

        self.parents.initialize()

    def update_product(self):
        ProductDialog(self.parents.user, self.product).exec()
        self.parents.initialize()


# ===================== Окно товаров =====================
class ProductsWindow(QMainWindow):
    def __init__(self, user=None):
        super().__init__()
        self.ui = Ui_ProductsWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))

        ui = self.ui

        self.user = user

        ui.FIO.setText(str(user) if user else "Гость")

        ui.comboBoxFilter.addItems(
            ["Все поставщики"] + list(set(p.seller for p in Product.objects.all()))
        )
        ui.comboBoxSort.addItems(["По возрастанию", "По убыванию"])

        ui.Search.textChanged.connect(self.initialize)
        ui.comboBoxSort.currentIndexChanged.connect(self.initialize)
        ui.comboBoxFilter.currentIndexChanged.connect(self.initialize)
        ui.Exit.clicked.connect(self.exit)
        ui.CreateProduct.clicked.connect(self.create_product)

        if Role.check_lvl(user) < 2:
            ui.CreateProduct.hide()

        self.initialize()

    def initialize(self):
        ui = self.ui

        layout = ui.scrollAreaWidgetContents.layout() or QVBoxLayout(ui.scrollAreaWidgetContents)

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        products = Product.objects.all()

        search = ui.Search.text().lower()
        sort = ui.comboBoxSort.currentText()
        filters = ui.comboBoxFilter.currentText()

        # 1. ФИЛЬТР
        if filters != "Все поставщики":
            products = products.filter(seller=filters)

        # 2. СОРТИРОВКА
        if sort == "По возрастанию":
            products = products.order_by("count")
        else:
            products = products.order_by("-count")

        # 3. ПОИСК
        if search.replace(" ", "") != "":
            products = products.filter(
                Q(name__icontains=search) |
                Q(article__icontains=search) |
                Q(description__icontains=search) |
                Q(supplier__icontains=search) |
                Q(seller__icontains=search) |
                Q(price__icontains=search) |
                Q(count__icontains=search) |
                Q(discount__icontains=search)
            )

        # Вывод
        for p in products:
            layout.addWidget(ProductFrame(p, self))

    def create_product(self):
        ProductDialog(self.user).exec()
        self.initialize()

    def exit(self):
        self.window = MainWindow()
        self.window.show()
        self.close()


# ===================== Диалог =====================
class ProductDialog(QDialog):
    def __init__(self, user, product=None):
        super().__init__()
        self.ui = Ui_ProductDialog()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        ui = self.ui

        self.user = user
        self.product = product

        ui.comboBoxCategory.addItems([c.name for c in Category.objects.all()])
        ui.comboBoxSupplier.addItems(list(set(p.supplier for p in Product.objects.all())))
        ui.comboBoxSeller.addItems(list(set(p.seller for p in Product.objects.all())))

        # Редактирование
        if product:
            p = product
            ui.Article.setText(p.article)
            ui.Name.setText(p.name)
            ui.Description.setText(p.description)
            ui.Price.setValue(p.price)
            ui.Count.setValue(p.count)
            ui.Discount.setValue(p.discount)

            ui.comboBoxCategory.setCurrentText(p.category.name if p.category else "")
            ui.comboBoxSupplier.setCurrentText(p.supplier)
            ui.comboBoxSeller.setCurrentText(p.seller)

            if p.image:
                ui.Path.setText(p.image.path)
                ui.Image.setPixmap(QPixmap(p.image.path))
                ui.Image.setScaledContents(True)

        ui.OpenFile.clicked.connect(self.open_file)
        ui.Save.clicked.connect(self.save)

    def open_file(self):
        ui = self.ui

        name, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Images *.jpeg *.jpg *.png"
        )

        if name:
            ui.Path.setText(name)
            ui.Image.setPixmap(QPixmap(name))
        else:
            ui.Path.setText("")
            ui.Image.setPixmap(QPixmap("picture.png"))

        ui.Image.setScaledContents(True)

    def save(self):
        ui = self.ui

        data = {
            "article": ui.Article.text().strip(),
            "name": ui.Name.text().strip(),
            "description": ui.Description.text().strip(),
            "category": ui.comboBoxCategory.currentText(),
            "supplier": ui.comboBoxSupplier.currentText(),
            "seller": ui.comboBoxSeller.currentText(),
        }

        price = ui.Price.value()
        path = ui.Path.text()

        if not all(data.values()):
            QMessageBox.warning(self, "Ошибка", "Не все поля заполнены")
            return

        if price <= 0:
            QMessageBox.warning(self, "Ошибка", "Цена не может быть 0")
            return

        p = self.product or Product()

        p.article = data["article"]
        p.name = data["name"]
        p.description = data["description"]
        p.category = Category.objects.filter(name=data["category"]).first()
        p.supplier = data["supplier"]
        p.seller = data["seller"]
        p.price = price
        p.count = ui.Count.value()
        p.discount = ui.Discount.value()

        # Картинка
        if path:
            filename = os.path.basename(path)

            # если новая картинка
            if not p.image or os.path.basename(p.image.name) != filename:

                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    with open(path, "rb") as f:
                        if p.image:
                            p.image.delete(save=False)
                        p.image.save(filename, File(f), save=False)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не верный формат изображения")

        # если убрали картинку
        elif p.image:
            p.image.delete(save=False)
        p.save()

        QMessageBox.information(self, "Успешно", "Сохранено")
        self.close()