#Modules___________________________________________________________________
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, escape
from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, IntegerField, validators, FileField, DateField
from datetime import datetime
from classes.user import User
from classes.cart import Cart
from classes.order import Order, OrderDetails
from classes.product import Product
from classes.business import Business
from classes.analytics import Analytics, BusinessAnalytics, ProductAnalytics
from classes.chatConvo import ChatConvo, TextMessage, OrderMessage
import os
from PIL import Image
import shutil
import shelve
import random
import requests

# Flask Config______________________________________________________________
DEBUG = False
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'ZDHX218H9H2KSOS36'


# Flask Page Routes_________________________________________________________
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    image_list = [
      'https://c.tenor.com/M8KokpeyuawAAAAj/niko-seal.gif',
      'https://c.tenor.com/ECpGYu8UAVkAAAAd/happy-fluffy.gif',
      'https://c.tenor.com/itCibgsuQSUAAAAd/seal-crying.gif',
      'https://c.tenor.com/SynOwLQzjfAAAAAd/seal-seals.gif',
      'https://c.tenor.com/aq8x-fzLKoMAAAAd/seal-white-seal.gif'
    ]
    #for fun, randomises image upon load
    image_url = image_list[random.randint(0, len(image_list)-1)]
    return render_template('error404.html', image_url=image_url), 404

# Rate Limiting
@app.errorhandler(429)
def too_many_requests(e):
    return render_template('error429.html'), 429

@app.errorhandler(500)
def internal_error(e):
    return render_template('error500.html'), 500

@app.route('/')
def home():
    return render_template('home.html',
                            businessTypes=Business.businessTypes.items(),
                            popularBusinesses=Business.get_popularBusinesses(),
                            enumerate=enumerate,
                            Business=Business)


@app.route('/getBusinessInfo', methods = ['GET'])
def ReturnJSON():
    if(request.method == 'GET'):
        businessID = escape(request.args.get('businessID').lower())
        businessObject = Business.get_businessByID(businessID)
  
        if businessObject:
          staffObjs = businessObject.get_businessStaff()
          staffDict = {}

          for i in staffObjs:
            staffDict[i.get_staffUserID()] = {}
            staffDict[i.get_staffUserID()]["Position"] = i.get_staffPosition()
          
          data = {
              "Name" : businessObject.get_businessName(),
              "Subject" : "Data Structures and Algorithms",
              "Email" : businessObject.get_businessEmail(),
               "Type" : businessObject.get_businessType(),
               "Number" :  businessObject.get_businessNumber(),
               "Staff" :  staffDict,
               "ID" :  businessID,
               "Description" :  businessObject.get_businessDescription()
          }
        else:
          data = {
              "Error" : "Invalid Business ID"
          }     
  
        return jsonify(data)

      
@app.route('/businessMenu', methods = ['POST', 'GET']) # displays the products
def businessMenu():
    user = User.get_LoggedInUser()
    if user:
        businessID = escape(request.args.get('businessID').lower())
        # Call GetBusinessInfo API Change URL name if project name changes   
      
        business = Business.get_businessByID(businessID)
        if business:
          # Log Analytics
          businessAnalytics = Analytics.get_AnalyticsObj(businessID, "business")
          if not businessAnalytics:
            businessAnalytics = BusinessAnalytics(businessID)
          businessAnalytics.add_visitor(user.get_userID())
          # Products
          products_list = Product.get_businessProducts(businessID)
          categories = []
          for product in products_list:
            product_category = product.get_category()
            if product_category not in categories:
                categories.append(product_category)
          print('Product categories for this business are', categories)


          return render_template('businessMenu.html',
                                business=business, products_list=products_list, categories=categories,businessID=businessID)
        else:
          flash('Error viewing business! Business may not exist', 'Error')
          return redirect('/')
    else:
        return render_template('accessDenied.html')


@app.route('/viewItem', methods = ['POST', 'GET'])
def viewItem():
    user = User.get_LoggedInUser()
    if user:
        businessID = escape(request.args.get('businessID').lower())
        productID = escape(request.args.get('productID').lower())
        product = Product.get_productByID(productID)
        return render_template('viewItem.html', businessID=businessID, product=product, productID=productID)
    else:
        return render_template('accessDenied.html')


@app.route('/cart')
def cart():
    user = User.get_LoggedInUser()

    if user:
        userCart = Cart.get_cartByUserID(user.get_userID())
        if userCart:
          products = userCart.get_products()
          userAddress = user.get_address()
          if userAddress:
            formattedAddress = f'{userAddress.get_line1()}, {userAddress.get_line2()}, {userAddress.get_city()} {userAddress.get_zipCode()}'
          else:
            formattedAddress = "No Saved Address"
            
          return render_template('cart.html',
                                  userCart=userCart,
                                  enumerate=enumerate,
                                  products=products,
                                  round=round,
                                  userAddress=formattedAddress, user=user)
        else:
          return render_template('cart.html')
    else:
        return render_template('accessDenied.html')


@app.route('/deleteCartProduct', methods=['GET'])
def deleteCartProduct():
    user = User.get_LoggedInUser()
    productArrayIndex = int(escape(request.args.get('productArrayIndex')))
    if user:
        cart = Cart.get_cartByUserID(user.get_userID())
        if cart.delete_product(productArrayIndex):
            if "numCartItems" in session:
              session["numCartItems"] = len(cart.get_products())
              if session["numCartItems"] == 0:
                session.pop('numCartItems', None)
            flash('Product deleted from cart!', 'Success')
            # Delete cart if Empty
            products = cart.get_products()
            if len(products) == 0:
                try:
                    cartDB = shelve.open('cart', 'c')
                    del cartDB[user.get_userID()]
                    cartDB.close()
                except Exception as e:
                    print(e)
            return redirect(url_for('cart'))
    else:
        return render_template('accessDenied.html')


@app.route('/orders')
def orders():
    user = User.get_LoggedInUser()
    if user:
        userID = user.get_userID()
        orders_list = Order.get_userAllOrders(userID)
        orderDetails_list = OrderDetails.get_userAllOrderDetails(userID)
        if orders_list == None or orderDetails_list == None:
            return render_template('orders/orders.html')
        else:
            return render_template('orders/orders.html',
                                   user=user,
                                   orderCount=len(orders_list),
                                   orders_list=orders_list,
                                   orderDetails_list=orderDetails_list, len=len)
    else:
        return render_template('accessDenied.html')


@app.route('/orderDetails', methods = ['GET'])  #USER VIEWING
def orderDetails():
    user = User.get_LoggedInUser()
    if user:
        orderID = escape(request.args.get('orderID').lower())
        #get orderID from the orders page
        order = Order.get_Order(orderID)
        if order:  #orderID is found
            print('Viewing order ID', orderID)
            orderDetails = OrderDetails.get_OrderDetails(orderID)
            products = order.get_products()
            return render_template('orders/orderDetails.html',
                                    user=user,
                                    order=order,
                                    orderDetails=orderDetails, products=products, enumerate=enumerate, float=float)
        else:
            flash('Error, no such order exists!', 'Error')
            return redirect(url_for('orders'))
    else:
        return render_template('accessDenied.html')

# Chats____________________________________________________________
@app.route('/chats')
def chats():
    user = User.get_LoggedInUser()
    if user:
        ChatConvoObjs = ChatConvo.get_usersChatConvos(user.get_userID())
        return render_template('chats/chats.html', ChatConvoObjs=ChatConvoObjs)
    else:
        return render_template('accessDenied.html')


@app.route('/createChatConvo', methods = ['GET'])
def createChatConvo():
    userID = escape(request.args.get('userID').lower())
    businessID = escape(request.args.get('businessID').lower())
    if userID and businessID:
        ChatObj = ChatConvo.get_chatConvoByUserIDandBusinessID(businessID, userID)
        if not ChatObj:
            # Create Chat
            chatConvo = ChatConvo(userID, businessID)
            return redirect(f'/chatConvo?chatConvoID={chatConvo.get_chatConvoID()}&POV=user')
        else:
            # Show Chat cos Already Exists
            return redirect(f'/chatConvo?chatConvoID={ChatObj.get_chatConvoID()}&POV=user')


@app.route('/sendTextMsg', methods = ['POST'])
def sendTextMsg():
        chatConvoID = request.form['chatConvoID'].lower()
        msgContent = request.form['msgContent'].lower()
        senderType = request.form['senderType'].lower()
        TextMessage(chatConvoID, senderType, msgContent)
        return redirect(request.referrer)


@app.route('/sendOrderMsg', methods=['GET'])
def sendOrderMsg():
    user = User.get_LoggedInUser()
    chatConvoID = escape(request.args.get('chatConvoID').lower())
    orderID = escape(request.args.get('orderID').lower())
    senderType = escape(request.args.get('senderType').lower())
    
    if user and orderID and chatConvoID:
        orderObj = Order.get_Order(orderID)
        OrderMessage(chatConvoID, senderType, orderObj)
        return redirect(request.referrer)
    else:
        return render_template('accessDenied.html')


@app.route('/deleteChat', methods=['GET'])
def deleteChat():
    user = User.get_LoggedInUser()
    chatConvoID = escape(request.args.get('chatConvoID').lower())
    if user and chatConvoID:
        if ChatConvo.deleteChat(chatConvoID):
            flash('Chat deleted!', 'Success')
            return redirect(url_for('chats'))
    else:
        return render_template('accessDenied.html')


@app.route('/chatConvo', methods=['GET'])
def chatConvo():
    user = User.get_LoggedInUser()
    if user:
        chatConvoID = escape(request.args.get('chatConvoID').lower())
        chatConvo = ChatConvo.get_chatConvoByID(chatConvoID)
        if chatConvo:
          POV = escape(request.args.get('POV').lower())
          if chatConvo:
              return render_template('chats/chatConvo.html',
                                    chatConvo=chatConvo,
                                    POV=POV)
    else:
        return render_template('accessDenied.html')


@app.route('/business')
def business():
    user = User.get_LoggedInUser()
    if user:
        business = Business.get_businessThatUserCanManage(user.get_userID())
        if business:
            businessID = business.get_businessID()
            
            # Products
            products_list = Product.get_businessProducts(businessID)
            productAnalytics = Analytics.get_AnalyticsObj(businessID, "product")
            if not productAnalytics:
                productAnalytics = ProductAnalytics(businessID)
            TopProductsDict = productAnalytics.get_top_products(businessID)

            # Orders
            order_list = Order.get_businessOrders(businessID)
            orderDetails_list = OrderDetails.get_businessOrderDetails(
                businessID)
            validStatuses = ['Processing','Shipping','Delivered']

            # Chats
            ChatConvoObjs = ChatConvo.get_businessChatConvos(businessID)

            return render_template('businessDashboard/businessDashboard.html',
                                   business=business,
                                   User=User,
                                   products_list = products_list,
                                   order_list=order_list,
                                   orderDetails_list=orderDetails_list,
                                   ChatConvoObjs=ChatConvoObjs,
                                   validStatuses = validStatuses,
                                   len=len,
                                   Analytics = Analytics,
                                   BusinessAnalytics=BusinessAnalytics,
                                   TopProductsDict=TopProductsDict)
        else:
            return render_template(
                'businessDashboard/businessRegistration.html', user=user, businessTypes=Business.businessTypes)
    else:
        return render_template('accessDenied.html')


@app.route('/editBusiness')
def editBusiness():
    user = User.get_LoggedInUser()
    if user:
        business = Business.get_businessThatUserCanManage(user.get_userID())
        if business:
            return render_template('businessDashboard/editBusiness.html',
                                   business=business,
                                   businessTypes=Business.businessTypes)
        else:
            return render_template('accessDenied.html')
            

@app.route('/addProduct')
def addProduct():
    user = User.get_LoggedInUser()
    if user:
        business = Business.get_businessThatUserCanManage(user.get_userID())
        if business:
            # Authenticated
            return render_template('businessDashboard/addProduct.html',
                                   user=user,
                                   business=business)
        else:
            flash('You are not authenticated with a business!', 'Error')
            return redirect('/business')
    else:
        return render_template('accessDenied.html')
   

@app.route('/viewProduct')
def viewProduct():
    user = User.get_LoggedInUser()
    if user:
        business = Business.get_businessThatUserCanManage(user.get_userID())
        if business:
            # Authenticated
            productID = escape(request.args.get('productID').lower())
            if productID:
              product = Product.get_productByID(productID)
              return render_template('businessDashboard/editProduct.html',
                                   user=user,
                                   business=business, product=product)
            else:
              return render_template('businessDashboard/businessDashboard.html')
        else:
            flash('You are not authenticated with a business!', 'Error')
            redirect('/business')
    else:
        return render_template('accessDenied.html')


@app.route('/deleteProduct')
def deleteProduct():
    user = User.get_LoggedInUser()
    if user:
        # Call deleteProduct API 
        productID = escape(request.args.get('productID').lower())
        productDeletionCheck = requests.delete("https://sellerseal-insecure.zacbytes.repl.co/api/deleteProduct", params={'productID':productID}).json()
        if productDeletionCheck["message"] == "success":
            print("WORKSSSS")
            flash('Product deleted!', 'Success')
            return redirect(url_for('business'))
        else:
            flash('Sorry, there was an error with deleting the product.', 'Danger')
    else:
        return render_template('accessDenied.html')


@app.route('/viewOrder')  #view order for businesses
def viewOrder():
    user = User.get_LoggedInUser()
    if user:
        orderID = escape(request.args.get('orderID').lower())
        order = Order.get_Order(orderID)
        #get orderID from the business orders page
        if order:  #order is found
            print('Viewing order ID', orderID, 'for business')  #test statement
            datenow = datetime.now().strftime(
                "%Y-%m-%d"
            )  #used so that can set minimum date for delivery date (cant be before today)
            orderDetails = OrderDetails.get_OrderDetails(orderID)
            products = order.get_products()
            try:
                usersDB = shelve.open('users', 'r')
                orderUserID = order.get_userID()
                orderUser = usersDB.get(orderUserID)
                usersDB.close()
            except Exception as e:
                print(e)
                flash('Error in reading user database', 'Error')
                return redirect('/business')
            else:
                return render_template('businessDashboard/viewOrder.html',
                                       orderUser=orderUser,
                                       order=order,
                                       orderDetails=orderDetails,
                                       orderID=orderID,
                                       todayDate=datenow,products=products, enumerate=enumerate, float=float)
        else:
            flash('Error, no such order exists!', 'Error')
            return redirect('/business')
    else:
        return render_template('accessDenied.html')


@app.route('/cancelOrder')
def cancelOrder():
    user = User.get_LoggedInUser()
    status = escape(request.args.get('status'))
    if user:
        try:
            orderID = escape(request.args.get('orderID').lower())
            order = OrderDetails.get_OrderDetails(orderID)
            order.set_orderStatus('Cancelled')
            ordersDB = shelve.open('orders', 'w')  #Rewrite to database
            orderDetails_dict = {}
            #Take current entries in database if they exist
            orderDetails_dict = ordersDB['OrderDetails']
            orderDetails_dict[orderID] = order
            ordersDB['OrderDetails'] = orderDetails_dict
            ordersDB.close()
        except Exception as e:
            print(e)
            flash('Error viewing order', 'Error')
        else:
            flash('Order successfully cancelled!', 'Success')
  
        if status == "businessCancel":
            return redirect('/business')
        else:
            return redirect('/orders')
    else:
        return render_template('accessDenied.html')


@app.route('/profile')
def profile():
    user = User.get_LoggedInUser()
    if user:
        return render_template('profile.html', user=user)
    else:
        return render_template('accessDenied.html')


@app.route('/logout')
def logout():
    [session.pop(key)
     for key in list(session.keys())]  # delete all session data
    return redirect(url_for('home'))


@app.route('/deleteAccount')
def deleteAccount():
    user = User.get_LoggedInUser()
    business = Business.get_businessThatUserCanManage(user.get_userID())
    if user:
        if business:
            flash('Cannot delete account while owning or managing a business.', 'Error')
            return redirect(url_for('profile'))
        else:
          if User.deleteUser(user.get_userID()):
              flash('Account deleted!', 'Success')
              return logout()
    else:
        return render_template('accessDenied.html')


@app.route('/deleteBusiness')
def deleteBusiness():
    user = User.get_LoggedInUser()
    if user:
        business = Business.get_businessThatUserCanManage(session["userID"])
        if Business.deleteBusiness(business.get_businessID()) and Product.deleteAllProducts(business.get_businessID()):
            flash('Business deleted!', 'Success')
            return redirect(url_for('home'))
    else:
        return render_template('accessDenied.html')


@app.route('/resetAnalytics')
def resetAnalytics():
    user = User.get_LoggedInUser()
    if user:
        business = Business.get_businessThatUserCanManage(session["userID"])
        businessID = business.get_businessID()
        try:
            analyticsDB = shelve.open('analytics', 'c')
            a = {}
            if "product" in analyticsDB:
              for id in analyticsDB["product"]:
                if id == businessID:
                  a = analyticsDB["product"]
                  del a[id]
              analyticsDB["product"] = a
            if "business" in analyticsDB:
              for id in analyticsDB["business"]:
                if id == businessID:
                  a = analyticsDB["business"]
                  del a[id]
              analyticsDB["business"] = a
            analyticsDB.close()
            flash('Analytics successfully reset!', 'Success')
        except Exception as e:
            print(e)
            flash('An error occured trying to reset the analytics.', 'Error')
        else:
            return redirect(url_for('business'))
    else:
        return render_template('accessDenied.html')

# API testing___________________________________________________
@app.route('/api/deleteProduct', methods=["DELETE"])
# eventually add authentication checks
def deleteProduct_api():
  productID = escape(request.args.get('productID').lower())
  if productID:
    product = Product.get_productByID(productID)
    if Product.deleteProduct(productID):
        return jsonify({"message":"success","productName":product.get_product_name()})
    else:
        return jsonify({"message":"error, no product found"}), 404
  else:
    return jsonify({"message":"error, no productID"}), 404

@app.route('/api/staff', methods=["POST"])
def addStaff_api():
  userID = escape(request.args.get('userID').lower())
  staffUserID = escape(request.args.get('staffUserID').lower())
  staffPosition = escape(request.args.get('staffPosition'))
  if not User.get_userByID(staffUserID): #no user returned, therefore user does not exist
      return jsonify({"message":"error, user does not exist"}), 404
  else:
      businessCheck = Business.get_businessThatUserCanManage(staffUserID) #to check if they are already part of a business
      if not businessCheck: #not in charge of business, validation complete
          business = Business.get_businessThatUserCanManage(userID)
          business.add_staff(staffUserID, staffPosition)
          return jsonify({"message":"success","staffID":staffUserID})
      else:
        return jsonify({"message":"error, user ID provided already in charge of a business"}), 400


@app.route('/api/staff', methods=["DELETE"])
def removeStaff_api():
    userID = escape(request.args.get('userID').lower())
    staffUserID = escape(request.args.get('staffUserID').lower())
    business = Business.get_businessThatUserCanManage(userID)
    if business.remove_staff(staffUserID):
        return jsonify({"message":"success","staffID":staffUserID})
    else:
        return jsonify({"message":"error, user does not exist"}), 404

    

# Flask WTForms Routes___________________________________________________
class RegisterForm(Form):
    name = StringField('Name:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=6, max=30)
                       ])
    email = StringField(
        'Email:', validators=[validators.DataRequired(),
                              validators.Email()])
    password = StringField('Password:',
                           validators=[
                               validators.DataRequired(),
                               validators.Length(min=6, max=20)
                           ])

    @app.route('/register', methods=['POST'])
    def register():
        form = RegisterForm(request.form)

        if form.validate():
            name = request.form['name']
            email = request.form['email'].lower()
            password = request.form['password']
            newUser = User(name, email, password)
            userID = newUser.get_userID()
            try:
                usersDB = shelve.open('users', 'c')
                if not User.get_userIDfromEmail(email):
                    usersDB[userID] = newUser
                    usersDB.close()
                    # Cache user data to flask session
                    session['email'] = email
                    session['name'] = name
                    session['userID'] = userID
                    shutil.copyfile('static/profilePictures/default.jpg',
                                    f'static/profilePictures/{userID}.jpg')
                    # Add to SQL
                    User.CreateUser_SQL(userID, email, password)
                    flash('Account created, welcome to SellerSeal!', 'Success')
                else:
                    flash('Email is already in use, please use another one.',
                          'Error')
            except Exception as e:
                print(e)
        # Redirect Back
        return redirect(request.referrer)


class LoginForm(Form):
    email = StringField(
        'Email:', validators=[validators.DataRequired(),
                              validators.Email()])
    password = StringField('Password:',
                           validators=[
                               validators.DataRequired(),
                               validators.Length(min=6, max=20)
                           ])

    @app.route('/login', methods=['POST'])
    def login():
        form = LoginForm(request.form)

        if form.validate():
            email = request.form['email'].lower()
            password = request.form['password']
            try:
                usersDB = shelve.open('users', 'c')
                userID = User.get_userIDfromEmail(email)
                if userID:
                    if User.attempt_Login(email, password):
                        # Logged In, set session vars
                        session['email'] = email
                        session['name'] = usersDB[userID].get_name()
                        session['userID'] = userID
                        cart = Cart.get_cartByUserID(userID)
                        if cart:
                          session["numCartItems"] = len(cart.get_products())
                        flash('Logged in!', 'Success')
                    else:
                        raise Exception("Password or email is invalid.")
                else:
                    raise Exception("Account does not exist.")
                usersDB.close()
            except Exception as e:
                print(e)
                flash(str(e), 'Error')
        # Redirect Back
        return redirect(request.referrer)


class EditProfileForm(Form):
    name = StringField('Name:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=6, max=30)
                       ])
    email = StringField(
        'Email:', validators=[validators.DataRequired(),
                              validators.Email()])
    line1 = StringField('Line 1:',
                        validators=[
                            validators.DataRequired(),
                            validators.Length(min=6, max=30)
                        ])
    line2 = StringField('Line 2:',
                        validators=[
                            validators.DataRequired(),
                            validators.Length(min=6, max=30)
                        ])
    city = StringField('City/Country:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=3, max=30)
                       ])
    zipCode = IntegerField('Zip Code:',
                           validators=[
                               validators.DataRequired(),
                               validators.NumberRange(min=0, max=9999999999)
                           ])

    @app.route('/editProfile', methods=['POST'])
    def editProfile():
        form = EditProfileForm(request.form)
        if form.validate():
            name = request.form['name']
            profilePic = request.files['pfp']
            email = request.form['email']
            line1, line2, city, zipCode = request.form['line1'], request.form[
                'line2'], request.form['city'], request.form['zipCode']

            try:
                usersDB = shelve.open('users', 'c')
                if session['userID'] in usersDB:

                    if User.newEmailNotInUse(
                            email
                    ):  # ensure new email not used by someone else
                        user = usersDB[session['userID']]
                        user.set_name(name)
                        user.set_email(email)
                        user.set_address(line1, line2, city, zipCode)
                        if os.path.exists(
                                f"static/profilePictures/{session['userID']}.jpg"
                        ):
                            os.remove(
                                f"static/profilePictures/{session['userID']}.jpg"
                            )

                        profilePic = Image.open(profilePic)
                        profilePic = profilePic.convert('RGB')
                        profilePic.save(
                            os.path.join('static/profilePictures',
                                         f"{session['userID']}.jpg"), optimize=True)
                        session['name'] = name

                        usersDB[session['userID']] = user
                        session['email'] = email
                        User.UpdateUser_SQL(session['userID'], email)

                        flash(
                            'Profile saved (Login with new email if needed).',
                            'Success')
                    else:
                        flash('Email already in use, please use another one.',
                              'Error')
                usersDB.close()
            except Exception as e:
                print(e)
        # Redirect Back
        return redirect(request.referrer)



class CreateOrderForm(Form):
    @app.route('/createOrder', methods=['POST'])
    def createOrder():
        userID = escape(request.args.get('userID').lower())
        user = User.get_userByID(userID)
        cart = Cart.get_cartByUserID(userID)
        cart_productIDs = cart.get_productIDs()
        form = CreateOrderForm(request.form)
        
        businessID = cart.get_businessID()

        if form.validate() and user:  #Submit form

            totalPrice = float(cart.get_totalPrice())
            pointsRedeemed = int(cart.get_pointsRedeemed())
            shippingAddress = user.get_address()

            

            try:
              
                #Creation of new Order Class
                newOrder = Order(userID, businessID)
                newOrder.set_totalPrice(totalPrice)
                newOrder.set_pointsRedeemed(pointsRedeemed)
                newOrder.set_products(cart.get_productIDs()) #Array of productIDS
                newOrder.calculatePrice()
                orderID = newOrder.get_orderID()
                print('Creating order', newOrder.get_orderID())

                #Creation of new OrderDetails Class
                newOrderDetails = OrderDetails(userID, businessID)
                newOrderDetails.set_orderID(orderID)
                newOrderDetails.set_products(cart_productIDs)
                newOrderDetails.set_discountPrice(cart.get_discountPrice())
                newOrderDetails.set_shippingAddress(shippingAddress.get_line1(),shippingAddress.get_line2(),shippingAddress.get_city(),shippingAddress.get_zipCode())
                #Give default shipping cost of 10 dollars
                newOrderDetails.set_shippingCost(10)
                newOrderDetails.calculatePrice()  #Calculate subtotal

                #Add/remove points earned to user
                pointsEarned = int(cart.get_pointsEarned())
                #pointsRedeemed declared earlier
                userPoints = 0
                userPoints += pointsEarned
                userPoints -= pointsRedeemed
                user.increment_points(userPoints)
                

                #Remove products from cart and deduct quantity
                product_list = []
                for productID in cart_productIDs:
                    product = Product.get_productByID(productID)
                    quantity = int(product.get_quantity()) #Originally string type
                    if quantity > 1: #In case multiple orders placed at same time to avoid negative quantity
                        product.set_quantity(str(quantity-1))
                        print('New quantity of ', product.get_product_name(), 'is', product.get_quantity())
                        product_list.append(product)
                    else:
                        #Out of stock
                        flash('Sorry, one of the items in your cart has run out of stock.', 'Error')
                        return redirect(request.referrer)

                    

                #========================= DATABASE WRITING ========================
                ordersDB = shelve.open('orders', 'c')
                orders_dict = {}
                orderDetails_dict = {}

                usersDB = shelve.open('users', 'c')
                productsDB = shelve.open('products', 'c')

                try:
                    #Take current entries in database if they exist
                    orders_dict = ordersDB['Orders']
                    orderDetails_dict = ordersDB['OrderDetails']
                except:
                    print('Error retrieving orders/orderDetails from DB')

                #Orders Dict
                orders_dict[newOrder.get_orderID()] = newOrder
                ordersDB['Orders'] = orders_dict

                #Order Details Dict
                orderDetails_dict[
                    newOrderDetails.get_orderID()] = newOrderDetails
                ordersDB['OrderDetails'] = orderDetails_dict
                ordersDB.close()

                #User DB
                usersDB[userID] = user
                usersDB.close()

                #Product DB
                for product in product_list:
                    productID = product.get_productID()
                    productsDB[productID] = product
                productsDB.close()

                #test statement
                print(
                    'Order created with ORDERID {}, pointsredeemed {}, totalprice{}, discountprice{}, businessID{}, pointsearned {}'
                    .format(newOrder.get_orderID(),
                            newOrder.get_pointsRedeemed(),
                            newOrder.get_totalPrice(),
                            newOrder.get_discountPrice(),
                            newOrder.get_businessID(),
                            newOrder.get_pointsEarned()))

            except Exception as e:
                print('Error', e)
                flash('An error occured creating the order, please try again',
                      'Error')
            else:
                Cart.delete_cartByUserID(userID)
                if "numCartItems" in session:
                  session.pop('numCartItems', None)
                flash('Order placed!', 'Success')
            # Redirect Back
            return redirect('/orders')


class EditOrderForm(Form):
    deliveryDate = DateField('Delivery Date:', format='%Y-%m-%d')
    orderStatus = SelectField('Order Status: ',
                              choices=[('Processing', 'Processing'),
                                       ('Shipping', 'Shipping'),
                                       ('Delivered', 'Delivered')])

    @app.route('/editOrder', methods=['POST'])
    def editOrder():
        orderID = escape(request.args.get('orderID').lower())
        form = EditOrderForm(request.form)
        if not form.validate():
            print('Error with validation')
            print(form.errors)

        user = User.get_LoggedInUser()

        if form.validate() and user:  #Submit form
            deliveryDate = request.form['deliveryDate']
            orderStatus = request.form['orderStatus']

            #Split date for consistency
            splitDate = deliveryDate.split('-')
            year = splitDate[0]
            month = splitDate[1]
            day = splitDate[2]
            newDeliveryDate = '{}/{}/{}'.format(day, month, year)

            try:
                ordersDB = shelve.open('orders', 'c')
                orderDetails_dict = {}
                #Take current entries in database if they exist
                orderDetails_dict = ordersDB['OrderDetails']
                selectedOrder = orderDetails_dict.get(orderID)
                selectedOrder.set_deliveryDate(newDeliveryDate)
                selectedOrder.set_orderStatus(orderStatus)
                selectedOrder.calculatePrice()  #Calculate new subtotal

                #Order Details Dict
                orderDetails_dict[selectedOrder.get_orderID()] = selectedOrder
                ordersDB['OrderDetails'] = orderDetails_dict
                ordersDB.close()
            except Exception as e:
                print('Error', e)
                flash('An error occured editing the order, please try again',
                      'Error')
                return redirect(request.referrer)
            else:
                flash('Order edited successfully!', 'Success')
                return redirect('/business')
        else:
            flash(
                'An error occured editing the order, please check fields are filled in',
                'Error')
            return redirect(request.referrer)


class BusinessRegisterForm(Form):
    businessName = StringField('Business Name:',
                               validators=[
                                   validators.DataRequired(),
                                   validators.Length(min=6, max=30)
                               ])
    businessDescription = StringField('Business Description:',
                            validators=[
                                validators.DataRequired(),
                                validators.Length(min=6, max=70)
                            ])
    businessEmail = StringField(
        'E-mail:', validators=[validators.DataRequired(),
                               validators.Email()])
    businessNumber = StringField(
        'Business Line:',
        validators=[validators.DataRequired(),
                    validators.Length(8)])

    @app.route('/businessRegister', methods=['POST'])
    def businessRegister():
        form = BusinessRegisterForm(request.form)
        if form.validate():
            businessName = request.form['businessName']
            businessDescription = request.form['businessDescription']
            businessEmail = request.form['businessEmail'].lower()
            businessNumber = request.form['businessNumber']
            businessLogo = request.files['logo']
            businessThumbnail = request.files['thumbnail']
            businessType = request.form['businessType']
            newBusiness = Business(businessName, businessDescription, businessEmail, businessNumber, businessType, session["userID"])
            businessID = newBusiness.get_businessID()
            try:
                businessDB = shelve.open('business', 'c')
                businessDB[businessID] = newBusiness
                businessDB.close()

                businessLogo = Image.open(businessLogo)
                businessLogo = businessLogo.convert('RGB')
                businessThumbnail = Image.open(businessThumbnail)
                businessThumbnail = businessThumbnail.convert('RGB')
                businessLogo.save(os.path.join('static/businessLogos', f"{businessID}.jpg"), optimize=True)
                flash('Business created, welcome to SellerSeal!', 'Success')
                businessThumbnail.save(os.path.join('static/businessThumbnails', f"{businessID}.jpg"), optimize=True)
                return redirect('/business')
            except Exception as e:
                print(e)
                flash('Error in accessing business database', 'Error')
                return redirect(request.referrer)

        else:  #Form not validated
            # Redirect Back
            flash(
                'Error in validating business, please check fields are correct',
                'Error')
            return redirect(request.referrer)


class EditBusinessForm(Form):
    businessName = StringField('Business Name:',
                               validators=[
                                   validators.DataRequired(),
                                   validators.Length(min=6, max=30)
                               ])
    businessDescription = StringField('Business Description:',
                            validators=[
                                validators.DataRequired(),
                                validators.Length(min=6, max=70)
                            ])
    businessEmail = StringField(
        'E-mail:', validators=[validators.DataRequired(),
                               validators.Email()])
    businessNumber = StringField(
        'Business Line:',
        validators=[validators.DataRequired(),
                    validators.Length(8)])

    @app.route('/editBusinessConfirm', methods=['POST'])
    def editBusinessConfirm():
        form = EditBusinessForm(request.form)
        if form.validate():
            businessName = request.form['businessName']
            businessDescription = request.form['businessDescription']
            businessEmail = request.form['businessEmail'].lower()
            businessNumber = request.form['businessNumber']
            businessLogo = request.files['logo']
            businessThumbnail = request.files['thumbnail']
            businessType = request.form['businessType']

            try:
                businessDB = shelve.open('business', 'c')
                user = User.get_LoggedInUser()
                business = Business.get_businessThatUserCanManage(
                    user.get_userID())
                businessID = business.get_businessID()
                business.set_businessName(businessName)
                business.set_businessDescription(businessDescription)
                business.set_businessEmail(businessEmail)
                business.set_businessNumber(businessNumber)
                business.set_businessType(businessType)

                #Business Logo override
                businessLogo = Image.open(businessLogo)
                businessLogo = businessLogo.convert('RGB')
                if os.path.exists(f"static/businessLogos/{businessID}.jpg"):
                    os.remove(f"static/businessLogos/{businessID}.jpg")
                businessLogo.save(
                    os.path.join('static/businessLogos', f"{businessID}.jpg"), optimize=True)

                #Business Thumbnail override
                businessThumbnail = Image.open(businessThumbnail)
                businessThumbnail = businessThumbnail.convert('RGB')
                if os.path.exists(f"static/businessThumbnails/{businessID}.jpg"):
                    os.remove(f"static/businessThumbnails/{businessID}.jpg")
                businessThumbnail.save(
                    os.path.join('static/businessThumbnails', f"{businessID}.jpg"), optimize=True)

                #Save to business DB
                businessDB[businessID] = business
                businessDB.close()
                return redirect('/business')
            except Exception as e:
                print(e)
                flash('Error opening business DB', 'Error')
                return redirect(request.referrer)


class AddBusinessStaffForm(Form):
    userID = StringField('User ID:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=50)
                         ])
    staffPosition = StringField('Staff Position:', validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=50)
                         ])

    
    @app.route('/addStaff', methods=['POST'])
    def addStaff():
        form = AddBusinessStaffForm(request.form)
        staffUserID = request.form['userID']
        staffPosition = request.form['staffPosition']
        if not form.validate():
            print('Error with validation:', form.errors)
            flash('An error occured validating the staff information, please try again', 'Error')
        else: #Form validated
            userID = User.get_LoggedInUser().get_userID()
            staffCheck = requests.post("https://sellerseal-insecure.zacbytes.repl.co/api/staff",
                                         params={
                                           'userID':userID,
                                           'staffUserID':staffUserID,
                                           'staffPosition':staffPosition}).json()  
            if staffCheck["message"] == "success":
                flash('Staff added!', 'Success')
            else:
                flash('An error occurred with adding a staff.', 'Danger')
        return redirect('/business')    

@app.route('/removeStaff', methods = ['GET'])
def removeStaff():
    staffID = escape(request.args.get('staffID').lower())
    userID = User.get_LoggedInUser().get_userID()
    staffCheck = requests.delete("https://sellerseal-insecure.zacbytes.repl.co/api/staff",
                                             params={
                                               'userID':userID,
                                               'staffUserID':staffID}).json()  
    if staffCheck["message"] == "success":
        flash('Staff removed successfully!', 'Success')
    else:
        flash('An error occurred with removing the staff.', 'Danger')  
    return redirect('/business')


class CreateProductForm(Form):
    product_name = StringField('Product Name:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=50)
                         ])
    quantity = IntegerField('Quantity:',
                           validators=[
                               validators.DataRequired(),
                               validators.NumberRange(min=0, max=9999999999)
                         ])
    price = IntegerField('Price:',
                           validators=[
                               validators.DataRequired(),
                               validators.NumberRange(min=0, max=999999999)
                        ])
    category = StringField('Category:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=50)
                         ])
    description = TextAreaField('Description:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=150)
                       ])
         

         
    @app.route('/createProduct', methods = ['POST'])
    def createProduct():
        create_product_form = CreateProductForm(request.form)
        if not create_product_form.validate():
            print('Error with validation:', create_product_form.errors)
            flash('An error occured validating the product, please try again', 'Error')
        else:
            product_name = request.form['product_name']
            price = request.form['price']
            quantity = request.form['quantity']
            category = request.form['category']
            description = request.form['description']
            product_image = request.files['product_image']

            #Business ID
            user = User.get_LoggedInUser()
            business = Business.get_businessThatUserCanManage(user.get_userID())
            businessID = business.get_businessID()

            newProduct = Product(product_name, quantity, price, category, description)
            newProduct.set_businessID(businessID)
            productID = newProduct.get_productID()

            try:
                db = shelve.open('products', 'c')
                product_image = Image.open(product_image)
                product_image.save(
                    os.path.join('static/productImages', f"{productID}.png"), optimize=True) # Saves product image
                db[productID] = newProduct
                print('Product was created!')
                db.close()
            except Exception as e:
                print(e) # prints the error
                flash("An error occurred creating the product! This may be because of database error or image uploaded was not compatitable", "Error")
            else:
                flash('Product successfully created!', 'Success')
        return redirect(url_for('business'))
        

class EditProductForm(Form):
    product_name = StringField('Product Name:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=50)
                         ])
    quantity = IntegerField('Quantity:',
                           validators=[
                               validators.DataRequired(),
                               validators.NumberRange(min=0, max=9999999999)
                         ])
    price = IntegerField('Price:',
                           validators=[
                               validators.DataRequired(),
                               validators.NumberRange(min=0, max=999999999)
                        ])
    category = StringField('Category:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=50)
                         ])
    description = TextAreaField('Description:',
                       validators=[
                           validators.DataRequired(),
                           validators.Length(min=1, max=150)
                       ])
    @app.route('/editProduct', methods = ['POST'])  
    def editProduct():  
        form = EditProductForm(request.form)
        if form.validate():
            productID = escape(request.args.get('productID').lower())
            product_name = request.form['product_name']
            price = request.form['price']
            category = request.form['category']
            quantity = request.form['quantity']
            description = request.form['description']
            product_image = request.files['product_image']
            
            product = Product.get_productByID(productID)
            product.set_product_name(product_name)
            product.set_price(price)
            product.set_quantity(quantity)
            product.set_category(category)
            product.set_description(description)
            try:
                db = shelve.open('products', 'c')

                if os.path.exists(f"static/productImages/{productID}.png"):
                    os.remove(f"static/productImages/{productID}.png")

                product_image = Image.open(product_image)
                product_image.save(
                    os.path.join('static/productImages', f"{productID}.png"), optimize=True)

                db[productID] = product
                db.close()
            except Exception as e:
                print(e)
                flash('Error opening products DB', 'Error')
            else:
                flash('Product successfully edited!', 'Success')
        else:
          flash('Error validating form!', 'Error')
        return redirect('/business')


class AddToCartForm(Form):    
    @app.route('/addToCart', methods = ['POST'])
    def addToCart():
        cartform = AddToCartForm(request.form)
        if request.method == 'POST' and cartform.validate():
            businessID = request.form['businessID']
            productID = request.form['productID'] 

            try:
                cart = Cart.get_cartByUserID(session["userID"])
                if not cart:
                    cart = Cart(session["userID"], businessID)

                businessOverrideCheck = cart.add_product(productID, businessID)
                if businessOverrideCheck == True: #business override
                    session["numCartItems"] = 1
                    flash('Cart has been reset, you can only add to cart items from the same business', 'Warning')
                else:
                    session["numCartItems"] = len(cart.get_products())

            except Exception as e:
                print('Error', e) # prints the error
                flash("Error in adding to cart", "Error")
            else:
                flash('Added to Cart!', 'Success')
        return redirect(f'/businessMenu?businessID={businessID}')


class SetCartPointsRedeemed(Form):    
    @app.route('/setCartPointsRedeemed', methods = ['POST'])
    def setCartPointsRedeemed():
        cartform = AddToCartForm(request.form)
        if request.method == 'POST' and cartform.validate():
            pointsRedeemed = request.form['pointsRedeemed']

            try:
                cart = Cart.get_cartByUserID(session["userID"])
                cart.set_pointsRedeemed(pointsRedeemed)
            except Exception as e:
                print(e)
                flash("Error redeeming points", "Error")
        return redirect('/cart')
    
    
# Flask Run_______________________________________________________________
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # REQUIRED for Repl.it
    )
