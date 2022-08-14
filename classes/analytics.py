import shelve
import classes.order as O
from classes.product import Product
from operator import itemgetter

class Analytics:
    """ This superclass is used for all analytics objects."""
    def __init__(self, id, AnalyticsType):
        #Analytics Types: 'business', 'product'
        self.id = id

        # Save to Shelve
        try:
            analyticsDB = shelve.open('analytics', 'c')
            analytics_dict = {}
            try:
                analytics_dict = analyticsDB[AnalyticsType]
            except:
                print('No existing', AnalyticsType, 'key found for initialising analytics')
            analytics_dict[self.id] = self
            analyticsDB[AnalyticsType] = analytics_dict
            #analyticsDB[AnalyticsType][self.id] = self
            analyticsDB.close()
        except Exception as e:
            print(e)

    # Additional Methods
    def get_AnalyticsObj(id, AnalyticsType):
        try:
            analyticsDB = shelve.open('analytics', 'c')
            analytics_dict = {}
            try:
                analytics_dict = analyticsDB[AnalyticsType]
            except:
                print('No existing', AnalyticsType, 'key found for getting analytics obj')
            analyticsDB.close()
            if id in analytics_dict:
                return analytics_dict[id]
        except Exception as e:
            print(e)


class BusinessAnalytics(Analytics):
    """ Subclass to store analytics for a business.
        - VISITORS
        - EARNINGS
    """
    def __init__(self, businessID):
        self.visitors = [] # Unique USER IDs
        super().__init__(businessID, "business")

    # Accessor Methods
    def get_visitors(self):
        return self.visitors

    # Mutator Methods
    def add_visitor(self, userID):
        if userID not in self.visitors:
            self.visitors.append(userID)  # save this
            
        try:
            analyticsDB = shelve.open('analytics', 'c')
            analytics_dict = {}
            try:
                analytics_dict = analyticsDB["business"]
            except:
                print('No existing business key found for adding visitor')
            analytics_dict[self.id] = self
            analyticsDB["business"] = analytics_dict
            analyticsDB.close()
        except Exception as e:
            print(e)


    # Additional Methods
    def calculate_earnings(businessID):
        orderDetailsList = O.OrderDetails.get_businessOrderDetails(businessID)
        earnings = 0

        if orderDetailsList:
            for orderDetail in orderDetailsList:
                earnings += orderDetail.get_subTotal()
        else:
            earnings = 0
            
        earnings = "{:.2f}".format(earnings)
        return earnings


class ProductAnalytics(Analytics):
    """ Subclass to store analytics for a product.
        - TIMES ORDERED (Add a function to calculate top 5 from this)
    """
    def __init__(self, businessID):
        self.productsOrdered = [] # Non-unique product IDs
        super().__init__(businessID, "product")

    # Mutator Methods
    def add_products(self, products): # Products must be an array
        for productID in products:
          self.productsOrdered.append(productID)
            
        try:
            analyticsDB = shelve.open('analytics', 'c')
            analytics_dict = {}
            try:
                analytics_dict = analyticsDB["product"]
            except:
                print('No existing business key found for adding product')
            analytics_dict[self.id] = self
            analyticsDB["product"] = analytics_dict
            analyticsDB.close()
        except Exception as e:
            print(e)

    # Accessor Methods
    def get_top_products(self, businessID):
      ProductsList = []
      TopProductsDict = {}

      for productObj in Product.get_businessProducts(businessID):
        ProductsList.append( productObj.get_productID() )


      for productID in self.productsOrdered:
        if productID in ProductsList:
          productName = Product.get_productByID(productID).get_product_name()

          if productName in TopProductsDict:
            TopProductsDict[productName] += 1
          else:
            TopProductsDict[productName] = 1


      # Convert to 1 DP
      if TopProductsDict:
          LargestValue = TopProductsDict[max(TopProductsDict, key=TopProductsDict.get)]
          
          for i in TopProductsDict:
            value = TopProductsDict[i]
            if value == LargestValue:
              TopProductsDict[i] = 1
            elif value/LargestValue:
              TopProductsDict[i] = max(min(1, value/LargestValue), 0.0)
      


      return dict(sorted(TopProductsDict.items(), key = itemgetter(1), reverse = True)[:5])

