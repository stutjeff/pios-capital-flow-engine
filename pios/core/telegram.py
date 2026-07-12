from __future__ import annotations
import os,requests

def send(text:str)->tuple[bool,str]:
    token=os.getenv('TELEGRAM_BOT_TOKEN','').strip(); chat=os.getenv('TELEGRAM_CHAT_ID','').strip()
    if not token or not chat:return False,'MISSING_TELEGRAM_SECRET'
    try:
        r=requests.post(f'https://api.telegram.org/bot{token}/sendMessage',json={'chat_id':chat,'text':text,'disable_web_page_preview':True},timeout=30)
        return (True,'SENT') if r.ok else (False,f'HTTP_{r.status_code}:{r.text[:200]}')
    except requests.RequestException as e:return False,f'NETWORK_ERROR:{e}'
