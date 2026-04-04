from app.db.supabase import supabase
from app.utils.hash import hash_password,verify_password
def create_user(user):
    user_dict= user.dict()
    user_dict['password']= hash_password(user_dict['password'])
    data = supabase.table('users').insert(user_dict).execute()
    return{
        "message":"User created successfully",
        "data": data.data
    }
def login_user(email,password):
    res= supabase.table("users").select("*").eq("email",email).execute()
    if not res.data:
        return {
            "message":"Invalid email or password"
        }
    user = res.data[0]
    if not verify_password(password,user['password']):
        return {"error":"Invalid email or password"}
    return {"message":"Login successful"}