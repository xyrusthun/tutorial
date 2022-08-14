import uuid
from datetime import datetime
import shelve
from classes.business import Business
from classes.user import User


class ChatConvo:
    """ This class is used for all chat conversations stored as own DB."""
    def __init__(self, userID, businessID):
        self.__chatConvoID = str(uuid.uuid4())  # generates random ID
        self.__userID = userID
        self.__businessID = businessID
        self.__messages = []  # Date, then timestamp, then message content and sender
        self.__creationTimeStamp = datetime.now()

        try:
            chatsDB = shelve.open('chats', 'c')
            chatsDB[self.__chatConvoID] = self
            chatsDB.close()
        except Exception as e:
            print(e)

    # Mutator Methods
    def add_message(self, msgObj):
      if msgObj:
          self.__messages.append(msgObj)
          return True


    # Accessor Methods
    def get_chatConvoID(self):
        return self.__chatConvoID

    def get_ChatTitle(self, POV):
        if POV.lower() == "user":
            business = Business.get_businessByID(self.__businessID)
            if business:
              return business.get_businessName()
            else:
              return "Deleted Business"
        else:
            user = User.get_userByID(self.__userID)
            if user:
                return user.get_name()
            else:
                return "Deleted User"



    def get_ordersBetweenUserAndBusiness(self):
        try:
          orders_list = []
          ordersDB = shelve.open('orders', 'c')
          orders_dict = ordersDB['Orders']
          ordersDB.close()

          for key in orders_dict:
            order = orders_dict.get(key)
            if order.get_businessID() == self.__businessID and order.get_userID() == self.__userID:
              orders_list.append(order)

          return orders_list

        except Exception as e:
          print(f'Error in reading orders DB: {e}')


    def get_ChatActivityDisplay(self):
        if len(self.__messages) > 0:
            msgObj = self.__messages[-1]
            daysDiff = int((datetime.now() - msgObj.get_timeStamp()).days)
            if daysDiff <= 0:
              return "Today"
            elif daysDiff <= 1:
              return "Yesterday"
            else:
              return f"{daysDiff} days ago"
        else:
           return ""


    def get_userID(self):
        return self.__userID

    def get_businessID(self):
        return self.__businessID

    def get_messages(self):
        return self.__messages

    def get_lastSentMessage(self):
        if len(self.__messages) > 0:
            msgObj = self.__messages[-1]
            if hasattr(msgObj, 'content'):
              return msgObj.content
            else:
              return "Sent order details..."
        else:
            return "No messages sent..."

    # Additional Methods
    def get_usersChatConvos(userID):
        chatObjs = []
        try:
            chatsDB = shelve.open('chats', 'c')
            for chatConvoID, chatObj in chatsDB.items():
              print(chatObj.get_userID())
              if chatObj.get_userID() == userID:
                chatObjs.append(chatObj)
            return chatObjs
            chatsDB.close()
        except Exception as e:
            print(e)

    def get_businessChatConvos(businessID):
        chatObjs = []
        try:
            chatsDB = shelve.open('chats', 'c')
            for chatConvoID, chatObj in chatsDB.items():
              #print(chatObj.get_businessID())
              if chatObj.get_businessID() == businessID:
                chatObjs.append(chatObj)
            return chatObjs
            chatsDB.close()
        except Exception as e:
            print(e)

    def get_chatConvoByID(chatConvoID):
        try:
            chatsDB = shelve.open('chats', 'c')
            if chatConvoID in chatsDB:
              return chatsDB[chatConvoID]
            chatsDB.close()
        except Exception as e:
            print(e)

    def get_chatConvoByUserIDandBusinessID(businessID, userID):
        try:
            chatsDB = shelve.open('chats', 'c')
            for chatConvoID, chatObj in chatsDB.items():
              #print(chatObj.get_businessID())
              if chatObj.get_businessID() == businessID and chatObj.get_userID() == userID:
                  return chatObj
            chatsDB.close()
        except Exception as e:
            print(e)
            

    def deleteChat(chatConvoID):
        try:
            chatsDB = shelve.open('chats', 'c')
            if chatConvoID in chatsDB:
                del chatsDB[chatConvoID]
            chatsDB.close()
            return True
        except Exception as e:
            print(e)




class ChatMessage():
    """ This superclass is used for all types of chat messages."""
    def __init__(self, chatConvoID, senderType):
        self.__senderType = senderType  # Business or User ONLY
        self.__timeStamp = datetime.now()

    # Accessor Methods
    def get_senderType(self):
      return self.__senderType

    def get_timeStamp(self):
      return self.__timeStamp


class TextMessage(ChatMessage):
    def __init__(self, chatConvoID, senderType, textMessage):
      super().__init__(chatConvoID, senderType)
      self.content = textMessage

      try:
          chatsDB = shelve.open('chats', 'c')
          chatConvo = chatsDB[chatConvoID]
          chatConvo.add_message(self)
          chatsDB[chatConvoID] = chatConvo
          chatsDB.close()
      except Exception as e:
          print(e)


class OrderMessage(ChatMessage):
    def __init__(self, chatConvoID, senderType, orderObj):
      super().__init__(chatConvoID, senderType)
      self.order = orderObj
      
      try:
          chatsDB = shelve.open('chats', 'c')
          chatConvo = chatsDB[chatConvoID]
          chatConvo.add_message(self)
          chatsDB[chatConvoID] = chatConvo
          chatsDB.close()
      except Exception as e:
          print(e)