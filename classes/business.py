import uuid
from flask import flash
import os
import shelve

class Business:
  """ This superclass is used for all businesses."""
  # All Business Types
  businessTypes = {"Food":"fas fa-utensils",
                  "Pets":"fas fa-paw",
                  "Jewellery":"far fa-gem",
                  "Toys":"fas fa-puzzle-piece",
                  "Books":"fas fa-book",
                  "Electronics":"fas fa-tv",
                  "Automotive":"fas fa-car-side",
                  "Non-Profit":"fas fa-ribbon",
                  "Stationery":"fas fa-pencil-ruler",
                  "Furniture":"fas fa-couch"
                  }

  def __init__(self, name, businessDescription, email, businessNumber, businessType, ownerID):
    self.__businessName = name
    self.__businessDescription = businessDescription
    self.__businessEmail = email
    self.__businessNumber = businessNumber
    self.__businessID = str(uuid.uuid4()) # generates random ID
    self.__businessAdmins = [] # stores userID of admins
    self.__businessType = businessType
    owner = Staff(ownerID, "Owner")
    self.__businessStaff = [owner]
    
  # Mutator Methods
  def set_businessName(self, name):
      self.__businessName = name

  def set_businessDescription(self, description):
      self.__businessDescription = description

  def set_businessEmail(self, email):
      self.__businessEmail = email

  def set_businessType(self, businessType):
      self.__businessType = businessType
      
  def set_businessNumber(self, businessNumber):
      self.__businessNumber = businessNumber

  def add_staff(self, staffUserID, staffPosition):
      staff = Staff(staffUserID, staffPosition)
      self.__businessStaff.append(staff)
      
      try:
          businessDB = shelve.open('business', 'c')
          if self.__businessID in businessDB:
              businessDB[self.__businessID] = self
          businessDB.close()
          flash('Staff user added!', 'Success')
      except Exception as e:
          print(e)

  def remove_staff(self, staffUserID):
      for staff in self.__businessStaff:
          if staff.get_staffUserID() == staffUserID:
            self.__businessStaff.remove(staff)
          
      try:
          businessDB = shelve.open('business', 'c')
          if self.__businessID in businessDB:
              businessDB[self.__businessID] = self
          businessDB.close()
      except Exception as e:
          print(e)

  # Accessor Methods
  def get_businessName(self):
      return self.__businessName
    
  def get_businessEmail(self):
      return self.__businessEmail

  def get_businessType(self):
      return self.__businessType

  def get_businessNumber(self):
      return self.__businessNumber

  def get_businessStaff(self):
      return self.__businessStaff

  def get_businessID(self):
      return self.__businessID

  def get_businessDescription(self):
      return self.__businessDescription
  
  
  # Additional Methods
  def get_businessThatUserCanManage(userID):
      # checks if userID is admin of specified business (to grant access)
      try:
          businessDB = shelve.open('business', 'c')

          for businessID, businessClass in businessDB.items():
            for staff in businessClass.get_businessStaff():
              if userID == staff.get_staffUserID():
                  return businessClass

          businessDB.close()
      except Exception as e:
          print(e)


  def get_businessByID(businessID):
      try:
          businessDB = shelve.open('business', 'c')
          if businessID in businessDB:
              return businessDB[businessID]
          businessDB.close()
      except Exception as e:
          print(e)


  def deleteBusiness(businessID):
      try:
          businessDB = shelve.open('business', 'c')
          if businessID in businessDB:
              del businessDB[businessID]
              if os.path.exists(f"static/businessLogos/{businessID}.jpg"):
                  os.remove(f"static/businessLogos/{businessID}.jpg")
          businessDB.close()
          return True
      except Exception as e:
          print(e)


  def get_popularBusinesses():
      ObjArray = []
      try:
          businessDB = shelve.open('business', 'c')
          for businessID, business in businessDB.items():
              ObjArray.append(business)
          businessDB.close()
          return ObjArray[0:3]
      except Exception as e:
          print(e)

  def get_allBusinesses():
      ObjArray = []
      try:
          businessDB = shelve.open('business', 'c')
          for businessID, business in businessDB.items():
              ObjArray.append(business)
          businessDB.close()
          return ObjArray
      except Exception as e:
          print(e)

  def get_BusinessesByCategory(category):
      ObjArray = []
      try:
          businessDB = shelve.open('business', 'c')
          for businessID, business in businessDB.items():
              if business.get_businessType().lower() == category.lower():
                ObjArray.append(business)
          businessDB.close()
          return ObjArray
      except Exception as e:
          print(e)


class Staff(Business):
  def __init__(self, staffUserID, staffPosition):
    self.__staffUserID = staffUserID
    self.__staffPosition = staffPosition


  # Mutator Methods
  def set_staffPosition(self, staffPosition):
    self.__staffPosition = staffPosition

  # Accessor Methods
  def get_staffPosition(self):
    return self.__staffPosition

  def get_staffUserID(self):
    return self.__staffUserID




