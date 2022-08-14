import uuid
import shelve
import os


class Product:
    count_id = 0

    def __init__(self, product_name, quantity, price, category, description):
        Product.count_id += 1
        self.productID = str(uuid.uuid4())
        self.__product_name = product_name
        self.__quantity = quantity
        self.__price = price
        self.__category = category
        self.__description = description
        self.__businessID = ''

    # Mutator Methods

    def set_product_name(self, product_name):
        self.__product_name = product_name

    def set_quantity(self, quantity):
        self.__quantity = quantity

    def set_price(self, price):
        self.__price = price

    def set_category(self, category):
        self.__category = category

    def set_description(self, description):
        self.__description = description

    def set_businessID(self, businessID):
        self.__businessID = businessID

    # Accessor Methods
    def get_productID(self):
        return self.productID

    def get_product_name(self):
        return self.__product_name

    def get_quantity(self):
        return self.__quantity

    def get_price(self):
        return self.__price

    def get_category(self):
        return self.__category

    def get_description(self):
        return self.__description

    def get_businessID(self):
        return self.__businessID

    # Additional Methods
    def get_businessProducts(businessID):
        try:
            products_list = []
            productsDB = shelve.open('products', 'c')

            for productID, product in productsDB.items():
                product_businessID = product.get_businessID()
                if product_businessID == businessID:
                    products_list.append(product)

            productsDB.close()
            return products_list

        except Exception as e:
            print(e)
            print('Error in reading product database')

    # Accessor Methods
    def get_product_businessID(self):
        return self.__product_businessID

    def get_productByID(productID):
        try:
            productsDB = shelve.open('products', 'r')
            product = productsDB.get(productID)
            productsDB.close()
            return product

        except Exception as e:
            print(f'Error in reading products DB: {e}')

    def deleteProduct(productID):
        try:
            productsDB = shelve.open('products', 'c')
            del productsDB[productID]
            productsDB.close()
            if os.path.exists(f"static/productImages/{productID}.png"):
                os.remove(f"static/productImages/{productID}.png")
            return True
        except Exception as e:
            print(f'Error in reading products DB: {e}')
    

    def deleteAllProducts(businessID):
        try:
            productsDB = shelve.open('products', 'c')

            for productID, product in productsDB.items():
                product_businessID = product.get_businessID()
                if product_businessID == businessID and productID in productsDB:
                    Product.deleteProduct(productID)
                    del productsDB[productID]

            productsDB.close()
            return True

        except Exception as e:
            print(e)
            print('Error in reading product database')

    

    