from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
from typing import List, Dict

app = FastAPI()

# 임시 인메모리 DB (실제 서비스 시 PostgreSQL 연동 필요)
users_db = {}

class User(BaseModel):
    user_id: int
    username: str
    coins: float = 0.0
    last_sync: datetime = datetime.now()
    shield_until: datetime = None
    raid_tickets: int = 3
    referred_by: int = None
    language_code: str = "en"

@app.post("/api/sync")
async def sync_coins(user_id: int):
    if user_id not in users_db:
        # 신규 유저 생성 로직
        users_db[user_id] = User(user_id=user_id, username=f"User_{user_id}")
    
    user = users_db[user_id]
    now = datetime.now()
    elapsed = (now - user.last_sync).total_seconds()
    
    # 초당 1코인 기본 적립 (밸런싱 가능)
    accumulated = elapsed * 1.0
    user.coins += accumulated
    user.last_sync = now
    return {"coins": user.coins, "raid_tickets": user.raid_tickets}

@app.post("/api/raid")
async def raid_friend(attacker_id: int, target_id: int):
    attacker = users_db.get(attacker_id)
    target = users_db.get(target_id)
    
    if not attacker or not target:
        raise HTTPException(status_code=404, detail="User not found")
    if attacker.raid_tickets <= 0:
        raise HTTPException(status_code=400, detail="No raid tickets left")
    if target.shield_until and target.shield_until > datetime.now():
        attacker.raid_tickets -= 1
        return {"status": "blocked", "message": "Target has a shield!"}

    # 강탈 로직: 타겟 코인의 10% ~ 30% 무작위 강탈
    raid_percent = random.uniform(0.1, 0.3)
    stolen_amount = target.coins * raid_percent
    
    target.coins -= stolen_amount
    attacker.coins += stolen_amount
    attacker.raid_tickets -= 1
    
    # 여기서 텔레그램 봇 API를 호출하여 타겟에게 '복수 알림' 발송 가능
    return {
        "status": "success",
        "stolen_amount": stolen_amount,
        "current_coins": attacker.coins
    }

@app.post("/api/invite")
async def invite_friend(inviter_id: int, new_user_id: int):
    if new_user_id in users_db:
        return {"status": "already_exists"}
    
    # 초대자 보상: 강탈권 +3, 코인 보너스
    if inviter_id in users_db:
        users_db[inviter_id].raid_tickets += 3
        users_db[inviter_id].coins += 1000
        
    return {"status": "success", "bonus": "3 tickets & 1000 coins"}