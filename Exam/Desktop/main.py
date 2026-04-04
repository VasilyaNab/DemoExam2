from django.db.models import Q
from django.core.files import File

from PySide6.QtWidgets import QMainWindow, QMessageBox, QFrame, QDialog, QFileDialog, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import QDate

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
    def check_lvl(user: User | None):
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

        self.ui.Login.setText("starka78@mail.ru")
        self.ui.Password.setText("9SdkLp012")

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

# ===================== Карточка товара =====================
class ProductFrame(QFrame):
    def __init__(self, product: Product, parents: "ProductsWindow"):
        super().__init__()
        self.ui = Ui_Product()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))

        self.product = product
        self.parents = parents

        # Заполняем поля
        category_name = product.category.name if product.category else ""
        self.ui.Type.setText(f"{category_name} | {product.name}")
        self.ui.Description.setText(self.ui.Description.text() + product.description)
        self.ui.Supplier.setText(self.ui.Supplier.text() + product.supplier)
        self.ui.Seller.setText(self.ui.Seller.text() + product.seller)
        self.ui.Count.setText(self.ui.Count.text() + str(product.count))
        self.ui.Discount.setText(str(product.discount) + self.ui.Discount.text())
        self.ui.NewPrice.setText(str(int(product.price * (1 - product.discount / 100))))
        if product.discount > 0:
            self.ui.OldPrice.setText(str(product.price))
        else:
            self.ui.OldPrice.hide()
        if product.discount > 15:
            self.ui.Discount.setStyleSheet("background-color:#2E8B57")
        else:
            self.ui.Discount.setStyleSheet("background-color:red")
        if product.count <= 0:
            self.ui.Count.setStyleSheet("color:#aaa")

        # Картинка
        pixmap = QPixmap("picture.png")
        if product.image and os.path.exists(product.image.name):
            pixmap = QPixmap(product.image.name)
        self.ui.Image.setPixmap(pixmap)
        self.ui.Image.setScaledContents(True)

        # Кнопки
        self.ui.Update.clicked.connect(self.update_product)
        self.ui.Delete.clicked.connect(self.delete_product)

        # Скрываем кнопки для роли < Админ
        if Role.check_lvl(parents.user) < 2:
            self.ui.Update.hide()
            self.ui.Delete.hide()

    def delete_product(self):
        if QMessageBox.question(self, "Удаление", "Вы точно хотите удалить этот товар?") == QMessageBox.Yes:
            if self.product.image:
                self.product.image.delete()
            self.product.delete()
        self.parents.load_products()

    def update_product(self):
        dialog = ProductDialog(self.parents.user, self.product)
        dialog.exec()
        self.parents.load_products()

# ===================== Окно товаров =====================
class ProductsWindow(QMainWindow):
    def __init__(self, user: User | None = None):
        super().__init__()
        self.ui = Ui_ProductsWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))

        self.user = user

        # Имя пользователя
        self.ui.FIO.setText(str(user) if user else "Гость")

        # Фильтры
        categories = ["Все категории"] + [c.name for c in Category.objects.all()]
        self.ui.comboBoxFilter.addItems(categories)
        self.ui.comboBoxSort.addItems(["Без сортировки", "По возрастанию цены", "По убыванию цены"])

        # Сигналы
        self.ui.Search.textChanged.connect(self.load_products)
        self.ui.comboBoxSort.currentIndexChanged.connect(self.load_products)
        self.ui.comboBoxFilter.currentIndexChanged.connect(self.load_products)
        self.ui.Exit.clicked.connect(self.exit)
        self.ui.CreateProduct.clicked.connect(self.create_product)

        # Скрываем кнопки по ролям
        if Role.check_lvl(user) < 2:
            self.ui.CreateProduct.hide()

        self.load_products()

    def load_products(self):
        layout = self.ui.scrollAreaWidgetContents.layout()
        if layout is None:
            layout = QVBoxLayout(self.ui.scrollAreaWidgetContents)
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        products = Product.objects.all()

        # Поиск
        search = self.ui.Search.text().lower()
        if search:
            products = products.filter(Q(name__icontains=search) | Q(article__icontains=search))

        # Фильтр
        category = self.ui.comboBoxFilter.currentText()
        if category != "Все категории":
            products = products.filter(category__name=category)

        # Сортировка
        sort_index = self.ui.comboBoxSort.currentIndex()
        if sort_index == 1:
            products = products.order_by("price")
        elif sort_index == 2:
            products = products.order_by("-price")

        # Добавляем карточки
        for p in products:
            frame = ProductFrame(p, self)
            layout.addWidget(frame)

    def create_product(self):
        dialog = ProductDialog(self.user)
        dialog.exec()
        self.load_products()

    def exit(self):
        self.window = MainWindow()
        self.window.show()
        self.close()

# ===================== Диалог добавления/редактирования =====================
class ProductDialog(QDialog):
    def __init__(self, user, product: Product | None = None):
        super().__init__()
        self.ui = Ui_ProductDialog()
        self.ui.setupUi(self)

        self.user = user
        self.product = product

        # Заполняем комбобоксы
        self.ui.comboBoxCategory.addItems([c.name for c in Category.objects.all()])
        self.ui.comboBoxSupplier.addItems(list(set(p.supplier for p in Product.objects.all())))
        self.ui.comboBoxSeller.addItems(list(set(p.seller for p in Product.objects.all())))

        # ЕСЛИ редактирование
        if self.product:
            p = self.product
            self.ui.Article.setText(p.article)
            self.ui.Name.setText(p.name)
            self.ui.Description.setText(p.description)
            self.ui.Price.setValue(p.price)
            self.ui.Count.setValue(p.count)
            self.ui.Discount.setValue(p.discount)

            self.ui.comboBoxCategory.setCurrentText(p.category.name if p.category else "")
            self.ui.comboBoxSupplier.setCurrentText(p.supplier)
            self.ui.comboBoxSeller.setCurrentText(p.seller)

            if p.image:
                self.ui.Path.setText(p.image.path)
                self.ui.Image.setPixmap(QPixmap(p.image.path))
                self.ui.Image.setScaledContents(True)

        self.ui.OpenFile.clicked.connect(self.open_file)
        self.ui.Save.clicked.connect(self.save)

    def open_file(self):
        name, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Images *.jpeg *.jpg *.png"
        )
        if name:
            self.ui.Path.setText(name)
            self.ui.Image.setPixmap(QPixmap(name))
            self.ui.Image.setScaledContents(True)
        else:
            self.ui.Path.setText("")
            self.ui.Image.setPixmap(QPixmap("./picture.png"))

    def save(self):
        ui = self.ui

        article = ui.Article.text().strip()
        name = ui.Name.text().strip()
        description = ui.Description.text().strip()
        category_name = ui.comboBoxCategory.currentText()
        supplier = ui.comboBoxSupplier.currentText()
        seller = ui.comboBoxSeller.currentText()

        price = ui.Price.value()
        count = ui.Count.value()
        discount = ui.Discount.value()
        path = ui.Path.text()

        # Проверки
        if not all([article, name, description, category_name, supplier, seller]):
            QMessageBox.warning(self, "Ошибка", "Не все поля заполнены")
            return

        if price <= 0:
            QMessageBox.warning(self, "Ошибка", "Цена не может быть равна 0")
            return

        # Новый или редактируемый
        p = self.product if self.product else Product()

        p.article = article
        p.name = name
        p.description = description
        p.category = Category.objects.filter(name=category_name).first()
        p.supplier = supplier
        p.seller = seller
        p.price = price
        p.count = count
        p.discount = discount

        # Картинка
        if path:
            filename = os.path.basename(path)
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                with open(path, "rb") as f:
                    if p.image:
                        p.image.delete(save=False)
                    p.image.save(filename, File(f), save=False)
            else:
                QMessageBox.warning(self, "Ошибка", "Не верный формат изображения")
        elif p.image:
            p.image.delete(save=False)

        p.save()

        QMessageBox.information(self, "Успешно", "Сохранено")
        self.close()