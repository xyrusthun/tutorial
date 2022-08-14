from classes.user import User
from classes.product import Product
from flask import session
import shelve

class Cart():
    """ Class to store User's cart products and information."""
    def __init__(self, userID, businessID):
      self.__userID = userID
      self.__businessID = businessID
      self.__products = [] # products IDs here
      self.__shippingCost = 10
      self.__totalPrice = 0 # Float value, total from products
      self.__discountPrice = 0 # discountPrice = totalPrice - pointsRedeemed discount
      self.__subTotal = 0 #Final subtotal, discountPrice + shippingCost
      self.__pointsRedeemed = 0 #200 points used = $1 saved
      self.__pointsEarned = 0 #$1 spent = 10 points

      try:
          cartDB = shelve.open('cart', 'c')
          cartDB[self.__userID] = self
          cartDB.close()
      except Exception as e:
          print(e)



    # Mutator Methods
    def add_product(self, productID, businessID):
        businessOverride = False #to track if business override
        if businessID == self.__businessID:
          self.__products.append(productID)
        else:
          # reset cart since business changed
          self.__products = [productID]
          self.__pointsRedeemed = 0
          if self.__businessID:
              #business ID exists, makes sure that does not display cart reset on no cart and only when cart already exists
              businessOverride = True
          self.__businessID = businessID

        self.calculatePrice()

        try:
            cartDB = shelve.open('cart', 'c')
            if self.__userID in cartDB:
                cartDB[self.__userID] = self
                cartDB.close()
                return businessOverride
        except Exception as e:
            print(e)

    def delete_product(self, ProductArrayIndex):
        del self.__products[ProductArrayIndex]
        self.calculatePrice()

        try:
            cartDB = shelve.open('cart', 'c')
            if self.__userID in cartDB:
                cartDB[self.__userID] = self
                return True
                cartDB.close()
        except Exception as e:
            print(e)

    def set_pointsRedeemed(self, pointsRedeemed):
        self.__pointsRedeemed = pointsRedeemed
        self.calculatePrice()
        try:
            cartDB = shelve.open('cart', 'c')
            if self.__userID in cartDB:
                cartDB[self.__userID] = self
                return True
                cartDB.close()
        except Exception as e:
            print(e)
    
    def calculatePrice(self):
        self.__totalPrice = 0
        self.__discountPrice = 0
        # Difference between totalPrice, discountPrice: totalPrice is only total calculated from products, discountPrice is for totalprice calculated with points redeemed

        for productID in self.__products:
          product  = Product.get_productByID(productID)
          self.__totalPrice += round(float(product.get_price()), 2)

        self.__pointsEarned = int(self.__totalPrice) * 10
        self.__discountPrice = round(float(self.__totalPrice) - (float(self.__pointsRedeemed) / 200), 2)
        self.__subTotal = round(float(self.__discountPrice) + float(self.__shippingCost), 2)

    


    # Accessor Methods
    def get_businessName(self):
        try:
            businessDB = shelve.open('business', 'c')
            if self.__businessID in businessDB:
                return businessDB[self.__businessID].get_businessName()
                businessDB.close()
        except Exception as e:
            print(e)
        
    def get_productIDs(self): # Returns ProductIDs in List
        products = []
        for productID in self.__products:
            products.append(productID)
        return products

    def get_products(self): # Returns Product Objs
        products = []
        for index, productID in enumerate(self.__products):
            productObj = Product.get_productByID(productID)
            if productObj:
                products.append(productObj)
            else:
                # Delete Product if Invalid
                if self.delete_product(index):
                  if "numCartItems" in session:
                    session["numCartItems"] = len(self.__products)
                    if session["numCartItems"] == 0:
                      session.pop('numCartItems', None)


        # Delete cart if Empty
        if len(products) == 0:
            try:
                cartDB = shelve.open('cart', 'c')
                del cartDB[self.__userID]
                cartDB.close()
            except Exception as e:
                print(e)

        return products

    def get_businessID(self):
        return self.__businessID

    def get_shippingCost(self):
        return round(self.__shippingCost, 2)

    def get_totalPrice(self):
        return round(self.__totalPrice, 2)

    def get_discountPrice(self):
        return self.__discountPrice

    def get_subTotal(self):
        return self.__subTotal

    def get_pointsRedeemed(self):
        return int(self.__pointsRedeemed)

    def get_pointsEarned(self):
        return round(self.__pointsEarned)

    def get_userCurrentPoints(self):
        user = User.get_userByID(self.__userID)
        if user:
          return user.get_points()
        else:
          return 0


    # Additional Methods
    def get_cartByUserID(userID):
        try:
            cartDB = shelve.open('cart', 'c')
            if userID in cartDB:
                return cartDB[userID]
                cartDB.close()
        except Exception as e:
            print(e)

    def delete_cartByUserID(userID):
        try:
            cartDB = shelve.open('cart', 'c')
            if userID in cartDB:
                del cartDB[userID]
                cartDB.close()
        except Exception as e:
            print(e)