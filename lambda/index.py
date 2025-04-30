# lambda/index.py
import json
import os
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError
import urllib.request

# モデルID
MODEL_ID = "https://7145-34-48-37-6.ngrok-free.app"

def lambda_handler(event, context):
    try:
        
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        print("Using model:", MODEL_ID)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # FastAPI用のリクエストペイロード
        request_payload = {
            "prompt": message,  # ユーザーからのメッセージを直接プロンプトとして使用
            "max_new_tokens": 256,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
                
        print("Calling FastAPI with payload:", json.dumps(request_payload))

        # FastAPI呼び出し
        url = f"{MODEL_ID}/generate"
        request = urllib.request.Request(
            url=url,
            data=json.dumps(request_payload).encode('utf-8'),  # JSONデータをバイト列に変換
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        # レスポンスを解析
        with urllib.request.urlopen(request) as response:
            response_body = json.loads(response.read().decode('utf-8'))

        print("FastAPI response:", json.dumps(response_body, default=str))
        
        # アシスタントの応答を取得
        assistant_response = response_body['generated_text']
        
        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }