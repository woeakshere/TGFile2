import motor, asyncio
import motor.motor_asyncio
from config import DB_URI, DB_NAME

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']
settings = database['settings']
banned_users = database['banned_users']
links_collection = database['links']

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

default_settings = {
    'header': '',
    'footer': '',
    'banner': '',
    'free_credits': 1,
    'token_duration': 86400,
    'button_enabled': False,
    'button_text': '',
    'button_url': ''
}

credits_collection = database['credits']

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }

async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return

async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})
    return

async def get_settings():
    doc = await settings.find_one({'_id': 'default'})
    if not doc:
        await settings.insert_one({'_id': 'default', **default_settings})
        doc = default_settings
    return doc

async def update_settings(**kwargs):
    await settings.update_one({'_id': 'default'}, {'$set': kwargs}, upsert=True)

async def ban_user(user_id: int):
    await banned_users.insert_one({'_id': user_id})

async def unban_user(user_id: int):
    await banned_users.delete_one({'_id': user_id})

async def is_banned(user_id: int):
    return bool(await banned_users.find_one({'_id': user_id}))

async def get_link(code: str):
    return await links_collection.find_one({'code': code})

async def save_link(code: str, ids: list, user_id: int):
    await links_collection.insert_one({
        'code': code,
        'ids': ids,
        'user_id': user_id,
        'disabled': False,
        'hits': 0
    })

async def increment_link_hits(code: str):
    await links_collection.update_one({'code': code}, {'$inc': {'hits': 1}})

async def set_link_disabled(code: str, disabled: bool):
    await links_collection.update_one({'code': code}, {'$set': {'disabled': disabled}})

async def delete_link(code: str):
    await links_collection.delete_one({'code': code})

async def get_credits_used(user_id: int):
    doc = await credits_collection.find_one({'_id': user_id})
    return doc.get('count', 0) if doc else 0

async def increment_credits_used(user_id: int):
    await credits_collection.update_one(
        {'_id': user_id},
        {'$inc': {'count': 1}},
        upsert=True
    )

async def reset_credits(user_id: int):
    await credits_collection.delete_one({'_id': user_id})

async def is_user_in_db(user_id: int):
    return bool(await credits_collection.find_one({'_id': user_id}))

async def bump_link_hits(code: str):
    await links_collection.update_one({'code': code}, {'$inc': {'hits': 1}})
    
