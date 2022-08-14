import uuid
from flask import session
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select
import os
import shelve

engine = create_engine('sqlite:///users_SQL')
meta = MetaData()
conn = engine.connect()
usersTable_SQL = Table(
   'users', meta, 
   Column('userID', String, primary_key = True), 
   Column('email', String), 
   Column('password', String),
)

print("these are columns in our table %s" %(usersTable_SQL.columns.keys()))


meta.create_all(engine)


class User:
    """ This superclass is used for all users."""
    def __init__(self, name, email, password):
        self.__name = name
        self.__userID = str(uuid.uuid4())
        self.__email = email
        self.__password = password
        self.__address = None
        self.__points = 0

    # Mutator Methods
    def set_name(self, name):
        self.__name = name

    def set_email(self, email):
        self.__email = email

    def set_address(self, line1, line2, city, zipCode):
        self.__address = UserAddress(line1, line2, city, zipCode)

    def increment_points(self, value):  # can be negative val.
        self.__points += value

    # Accessor Methods
    def get_name(self):
        return self.__name

    def get_email(self):
        return self.__email
      
    def get_address(self):
        return self.__address


    def get_points(self):
        return self.__points

    def get_userID(self):
        return self.__userID

    # Additional Methods
    def get_LoggedInUser():
        try:
            usersDB = shelve.open('users', 'c')
            if session['userID'] in usersDB:
                return usersDB[session['userID']]
            else:
                raise Exception("User does not exist.")
            usersDB.close()
        except Exception as e:
            print(e)


    def get_userByID(userID):
      try:
          usersDB = shelve.open('users', 'c')
          if userID in usersDB:
              return usersDB[userID]
          usersDB.close()
      except Exception as e:
          print(e)
          

    def newEmailNotInUse(email):
        try:
            usersList = []
            usersDB = shelve.open('users', 'c')

            for userID, userClass in usersDB.items():
                usersList.append(userClass.get_email())

            usersList.remove(session['email'])
            if email in usersList:
                return False  # because duplicate
            else:
                return True
                
            usersDB.close()
        except Exception as e:
            print(e)
            

    def deleteUser(userID):
        try:
            usersDB = shelve.open('users', 'c')
            if userID in usersDB:
                del usersDB[userID]
                usersDB.close()
                if os.path.exists(f"static/profilePictures/{userID}.jpg"):
                    os.remove(f"static/profilePictures/{userID}.jpg")
                User.DeleteUser_SQL(userID)
            return True
        except Exception as e:
            print(e)

          
    # SQL Methods
    def CreateUser_SQL(userID, email, password):
      conn = engine.connect()
      ins = usersTable_SQL.insert().values(userID = userID, email = email, password = password)
      result = conn.execute(ins)
      print(result)
    
    def DeleteUser_SQL(userID):
      conn = engine.connect()
      conn.execute(usersTable_SQL.delete().where(usersTable_SQL.c.userID == userID))
    
    def UpdateUser_SQL(userID, newEmail):
      conn = engine.connect()
      conn.execute(usersTable_SQL.update().where(usersTable_SQL.c.userID==userID).values(email="newEmail"))
    
    def GetUser_SQL(email):
      conn = engine.connect()
      result = conn.execute(usersTable_SQL.select().where(usersTable_SQL.c.email == email))
      if result:
        return result.fetchall()

    def get_userIDfromEmail(email):
      try:   
        conn = engine.connect()
        result = conn.execute(select(usersTable_SQL.c.userID).where(usersTable_SQL.c.email == email)).first()
        if result:
          return result[0]
        else:
          return False
      except Exception as e:
        print(e)

    def attempt_Login(email, password):
      try:
        conn = engine.connect()
        # SQL INJECTION:   ' OR 'a'='a';--
        result = conn.execute( "SELECT * FROM users WHERE email = '%s' AND password = '%s'" % (email, password) ).first()
        if result:
          return result
        else:
          return False
      except Exception as e:
        print(e)




class UserAddress(User):
    """ Subclass to store User's saved shipping address."""
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