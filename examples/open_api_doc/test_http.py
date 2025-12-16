import requests
import json


def query_garden_weather(group_id, user_id="0", user_realm="1", 
                         accept_language="zh-CN", terminal=1, time_zone=None, 
                         package_name=None, language=None):

    # API基础URL
    base_url = "http://api-dev.fairlandiot.com:9080/fyld-device-api"
    endpoint = "/deviceGroupApi/gardenWeather"
    url = f"{base_url}{endpoint}"
    
    # 请求头
    headers = {
        "userId": user_id,
        "userRealm": user_realm,
        "Accept-Language": accept_language,
        "terminal": str(terminal),
        "Content-Type": "application/json"
    }
    
    # 可选的请求头
    if package_name:
        headers["packageName"] = package_name
    if time_zone:
        headers["timeZone"] = time_zone
    
    # 请求体
    request_body = {
        "groupId": group_id
    }
    
    # 可选的请求体字段
    if time_zone:
        request_body["timeZone"] = time_zone
    if language:
        request_body["language"] = language
    
    try:
        # 发送POST请求
        response = requests.post(
            url=url,
            headers=headers,
            json=request_body,
            timeout=5
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 返回JSON响应
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        if hasattr(e.response, 'text'):
            print(f"响应内容: {e.response.text}")
        raise


# 示例使用
if __name__ == "__main__":
    # 示例参数
    group_id = 12345  # 替换为实际的庭院Id
    
    # 调用API
    result = query_garden_weather(
        group_id=group_id,
        user_id="0",
        user_realm="1",
        accept_language="zh-CN",
        terminal=1
    )
    
    # 打印结果
    print("API响应:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 解析响应数据
    if result.get("code") == 200 or result.get("code") == 0:
        data = result.get("data", {})
        print("\n天气信息:")
        print(f"温度: {data.get('temperature')}°C")
        print(f"主要天气: {data.get('mainWeather')}")
        print(f"湿度: {data.get('humidity')}%")
        print(f"空气质量: {data.get('aqi')}")
        print(f"日出时间: {data.get('sunrise')}")
        print(f"日落时间: {data.get('sunset')}")
    else:
        print(f"请求失败: {result.get('msg')}")
