import uuid
import shelve
from classes.business import Business
from classes.product import Product
import classes.analytics as A
from classes.user import User
from datetime import datetime # used for order and delivery dates

class Order:
  """ Class used by orders, viewed by customer and edited by business"""
  def __init__(self, userID, businessID):
    self.orderID = str(uuid.uuid4()) # generates random ID
    self.__businessID = businessID
    self.__products = [] # products IDs here
    self.__userID = userID # customer userID here
    self.totalPrice = 0 # Float value
    self.__discountPrice = 0
    #Difference between totalPrice, discountPrice and subtotal: totalPrice is only total calculated from products, discountPrice is for totalprice calculated with points redeemed
    self.__pointsRedeemed = 0 #200 points used = $1 saved
    self.__pointsEarned = 0 #$1 spent = 10 points


  # Mutator Methods
  def set_businessID(self, businessID):
    self.__businessID = businessID

  def set_products(self, products):
    for productID in products:
        self.__products.append(productID) #Product array format

    # Log Analytics
    productAnalytics = A.Analytics.get_AnalyticsObj(self.__businessID, "product")
    #print(productAnalytics)
    if not productAnalytics:
      productAnalytics = A.ProductAnalytics(self.__businessID)
    productAnalytics.add_products(products)

  def set_userID(self, userID):
    self.__userID = userID

  def set_totalPrice(self, totalPrice):
    self.totalPrice = totalPrice

  def set_discountPrice(self, discountPrice):
    self.discountPrice = discountPrice

  def set_pointsRedeemed(self, pointsRedeemed):
    self.__pointsRedeemed = pointsRedeemed

  def set_pointsEarned(self, pointsEarned):
    self.__pointsEarned = pointsEarned


  # Accessor Methods
  def get_orderID(self):
    return self.orderID

  def get_businessID(self):
    return self.__businessID

  def get_products(self): # Returns Product Objs
      products = []
      for productID in self.__products:
          productObj = Product.get_productByID(productID)
          products.append(productObj)

      return products

  def get_productIDs(self): # Returns ProductIDs in List
      return self.__products

  def get_userID(self):
    return self.__userID

  def get_totalPrice(self):
    return self.totalPrice

  def get_discountPrice(self):
    return self.discountPrice

  def get_pointsRedeemed(self):
    return self.__pointsRedeemed

  def get_pointsEarned(self):
    return self.__pointsEarned

  def get_businessName(self):
    business = Business.get_businessByID(self.get_businessID())
    if business:
        businessName = business.get_businessName()
        return businessName
    else:
        return 'Deleted Business'

  def get_customerName(self):
    customer = User.get_userByID(self.get_userID())
    if customer:
        customerName = customer.get_name()
        return customerName
    else:
        return 'No name'

  # Additional Methods
  def calculatePrice(self):
    try:
      totalPrice = self.get_totalPrice()
      pointsRedeemed = self.get_pointsRedeemed()
      maxPoints = round(totalPrice * 200)
      calcPrice = totalPrice
      
      if pointsRedeemed != 0:
        if pointsRedeemed <= maxPoints:
          calcPrice = round((totalPrice - (pointsRedeemed / 200)),2)
        else: #Max points exceed
          calcPrice = 0
          remainingPoints = pointsRedeemed - maxPoints
          return remainingPoints

      self.set_discountPrice(calcPrice)

      #Points earned
      #Takes totalprice * 10
      calcPoints = round(totalPrice * 10)
      #print('Points calculated are', calcPoints)
      self.set_pointsEarned(calcPoints)
    except ValueError:
      print('Value error, check price and points are not invalid type')
  #Calculates discountPrice, totalprice with discounts before adding delivery cost

  def get_userAllOrders(userID):
    #Retrieving of user orders
    try:
      orders_list = []
      orders_dict = {}
      ordersDB = shelve.open('orders', 'c')
      orders_dict = ordersDB['Orders']
      ordersDB.close()

      for key in orders_dict:
        order = orders_dict.get(key)
        if order.get_userID() == userID:
          orders_list.append(order)

      return orders_list

    except Exception as e:
      print(f'Error in reading orders DB: {e}')


  def get_businessOrders(businessID): # Collects all the orders for 1 business and puts it into a list
    #Retrieving of Business Orders
    try:
      orders_list = []
      orders_dict = {}
      ordersDB = shelve.open('orders', 'c')
      orders_dict = ordersDB['Orders']
      ordersDB.close()

      for key in orders_dict:
        order = orders_dict.get(key)
        if order.get_businessID() == businessID:
          orders_list.append(order)

      return orders_list

    except Exception as e:
      print(f'Error in reading orders DB: {e}')


  def get_Order(orderID):
    #Returns order via OrderID
    try:
      orders_dict = {}
      ordersDB = shelve.open('orders', 'c')
      orders_dict = ordersDB['Orders']
      ordersDB.close()

      orderSelected = orders_dict.get(orderID)
      return orderSelected
    except Exception as e:
      print(f'Error in reading orders DB: {e}')





class OrderDetails(Order):
  """ Class used by orders for more specific details"""
  def __init__(self, userID, businessName):
    super().__init__(userID, businessName) #inheritance
    self.__orderStatus = 'Processing' #Can be 'Processing','Shipping','Delivered' or 'Cancelled'
    self.__orderDate = datetime.today().strftime('%d/%m/%Y %H:%M')
    self.__shippingCost = 0 #Float
    self.__shippingAddress = None #Uses OrderShippingAddress Subclass
    self.__deliveryDate = ''
    self.__subTotal = 0 #Float


  #Mutator Methods
  def set_orderID(self, orderID):
    self.orderID = orderID

  def set_orderStatus(self, orderStatus):
    self.__orderStatus = orderStatus

  def set_orderDate(self, orderDate):
    self.__orderDate = orderDate

  def set_shippingCost(self, shippingCost):
    self.__shippingCost = shippingCost

  def set_shippingAddress(self, line1, line2, city, zipCode):
    self.__shippingAddress = OrderShippingAddress(line1, line2, city, zipCode)

  def set_deliveryDate(self, deliveryDate):
    self.__deliveryDate = deliveryDate

  def set_subTotal(self, subTotal):
    self.__subTotal = subTotal


  #Accessor Methods
  def get_orderStatus(self):
    return self.__orderStatus

  def get_orderDate(self):
    return self.__orderDate

  def get_shippingCost(self):
    return self.__shippingCost

  def get_shippingAddress(self):
    return self.__shippingAddress

  def get_deliveryDate(self):
    return self.__deliveryDate

  def get_subTotal(self):
    return self.__subTotal

  #Additional Methods
  def calculatePrice(self):  #Polymorphism
    try:
      calcPrice = round((self.get_discountPrice() + self.get_shippingCost()),2)
      self.set_subTotal(calcPrice)

    except ValueError:
      print('Value error, totalPrice and shippingCost may be invalid types')
  #calculatePrice method, calculates subtotal after adding delivery cost

  def formatDate(self, givenDate):
    #Takes either delivery or order date and formats it for html use
    splitDate = givenDate.split('/') 
    year = splitDate[2]
    year = year[:4] #Year truncation (for orderDate)
    splitDate[2] = year
    day = splitDate[0]
    month = splitDate[1]
    newDate = '{}-{}-{}'.format(year,month,day)
    return newDate

  def get_userAllOrderDetails(userID):
    #Retrieving of user orders
    try:
      orderDetails_list = []
      orderDetails_dict = {}
      ordersDB = shelve.open('orders', 'c')
      orderDetails_dict = ordersDB['OrderDetails']
      ordersDB.close()

      for key in orderDetails_dict:
        orderDetails = orderDetails_dict.get(key)
        if orderDetails.get_userID() == userID:
          orderDetails_list.append(orderDetails)

      return orderDetails_list

    except Exception as e:
      print(f'Error in reading orders DB: {e}')

  def get_businessOrderDetails(businessID): # Collects all order details for 1 business puts it into list
    #Retrieving of Business Orders
    try:
      orderDetails_list = []
      orderDetails_dict = {}
      ordersDB = shelve.open('orders', 'c')
      orderDetails_dict = ordersDB['OrderDetails']
      ordersDB.close()

      for key in orderDetails_dict:
        orderDetails = orderDetails_dict.get(key)
        if orderDetails.get_businessID() == businessID:
          orderDetails_list.append(orderDetails)

      return orderDetails_list

    except Exception as e:
      print(e)
      print('Error in reading order database')

  def get_OrderDetails(orderID):
    #Returns order via OrderID
    try:
      orderDetails_dict = {}
      ordersDB = shelve.open('orders', 'c')
      orderDetails_dict = ordersDB['OrderDetails']
      ordersDB.close()

      orderDetailsSelected = orderDetails_dict.get(orderID)
      return orderDetailsSelected
    except Exception as e:
      print(e)
      print('Error in reading order database')


class OrderShippingAddress(Order):
  """ Subclass to store order's shipping address."""
  def __init__(self, line1, line2, city, zipCode):
    self.__line1 = line1
    self.__line2 = line2
    self.__city = city
    self.__zipCode = zipCode

  # Accessor Methods
  def get_line1(self):
    return self.__line1

  def get_line2(self):
    return self.__line2

  def get_city(self):
    return self.__city

  def get_zipCode(self):
    return self.__zipCode