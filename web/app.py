from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy
app= Flask(__name__)
api= Api(app)
client= MongoClient("mongodb://db:27017")

db= client.similarityDB
users= db["Users"]

def UserExist(username):
    if users.find({"username":username}).count()==0:
        return False
    else:
        return True

def verifyPw(username,password):
    if not UserExist(username):
        return False
    hashed_pw = users.find({"username":username})[0]["password"]

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw)== hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({"username":username})[0]["tokens"]
    return tokens

class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username= postedData["username"]
        password= postedData["password"]

        if UserExist(username):
            retJson= {
                "status": 301,
                "msg":"Invalid Username"
            }
            return jsonify(retJson)

        hashed_pw= bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())
        users.insert({
            "username": username,
            "password":hashed_pw,
            "tokens":5
        })
        retJson={
            "status":200,
            "msg": "You have successfully signed up to the API"
        }
        return jsonify(retJson)

class Detect(Resource):
    def post(self):
        postedData= request.get_json()
        username= postedData["username"]
        password= postedData["password"]
        text1 = postedData["text1"]
        text2= postedData["text2"]

        if not UserExist(username):
            retJson= {
                "status": 301,
                "msg": "Inavlid Username"
            }
            return jsonify(retJson)

        correct_pw = verifyPw(username,password)
        if not correct_pw:
            retJson={
                "status":302,
                "msg": "Invalid Password"
            }
            return jsonify(retJson)
        num_tokens = countTokens(username)
        if num_tokens <=0:
            retJson= {
                "status": 303,
                "msg": "You are out of token please refill"
         }
            return jsonify(retJson)

        # Calculating edit distance
        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2= nlp(text2)

        ratio= text1.similarity(text2)
        retJson={
            "status":200,
            "similarity": ratio,
            "msg": "Similarity score calculated successfully"
     }
        current_tokens = countTokens(username)
        users.update(
         {"username":username},
            {"$set":{"tokens":current_tokens-1}}
        )
        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData= request.get_json()
        username= postedData["username"]
        password= postedData["admin_pw"]
        refill_amount= postedData["refill"]

        if not UserExist(username):
            retJson ={
                "status":301,
                "msg": "Invalid username"
            }
            return jsonify(retJson)
        correct_pw ="1234"
        if not password== correct_pw:
            retJson ={
                "status": 304,
                "msg": "Invalid Admin Password"
            }
            return jsonify(retJson)
        current_tokens = countTokens(username)
        users.update({"username":username},
                     {"$set":{"tokens":refill_amount+current_tokens}
                     })

        retJson= {
            "status": 200,
            "msg": "Refilled Successfully"
        }
        return jsonify(retJson)

api.add_resource(Register,'/register')
api.add_resource(Detect,'/detect')
api.add_resource(Refill,'/refill')

if __name__=='__main__':
    app.run(host='0.0.0.0')