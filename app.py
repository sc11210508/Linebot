from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,
    CreateRichMenuAliasRequest
)
import os

# 设置配置
access_token = os.getenv('CHANNEL_ACCESS_TOKE')
if not access_token:
    raise ValueError("Environment variable 'CHANNEL_ACCESS_TOKEN' not set.")
configuration = Configuration(access_token=access_token)

def create_rich_menu(api_client, menu_data, image_path, alias_id):
    """
    创建图文选单并上传图片，设置别名。
    """
    line_bot_api = MessagingApi(api_client)
    line_bot_blob_api = MessagingApiBlob(api_client)

    # 创建图文选单
    rich_menu_id = line_bot_api.create_rich_menu(
        rich_menu_request=RichMenuRequest.from_json(menu_data)
    ).rich_menu_id

    # 上传图文选单图片
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    with open(image_path, 'rb') as image:
        line_bot_blob_api.set_rich_menu_image(
            rich_menu_id=rich_menu_id,
            body=bytearray(image.read()),
            _headers={'Content-Type': 'image/png'}
        )

    # 设置图文选单别名
    line_bot_api.create_rich_menu_alias(
        CreateRichMenuAliasRequest(
            rich_menu_alias_id=alias_id,
            rich_menu_id=rich_menu_id
        )
    )
    return rich_menu_id

with ApiClient(configuration) as api_client:
    # 图文选单 A 数据
    rich_menu_a_str = """{
        "size": {
            "width": 2500,
            "height": 1686
        },
        "selected": true,
        "name": "图文选单 A",
        "chatBarText": "查看更多信息",
        "areas": [
            {
                "bounds": { "x": 0, "y": 0, "width": 833, "height": 843 },
                "action": {
                    "type": "richmenuswitch",
                    "richMenuAliasId": "richmenu_b",
                    "data": "richmenu-changed-to-b"
                }
            },
            {
                "bounds": { "x": 834, "y": 0, "width": 833, "height": 843 },
                "action": { "type": "message", "text": "B" }
            }
        ]
    }"""

    # 图文选单 B 数据
    rich_menu_b_str = """{
        "size": {
            "width": 2500,
            "height": 1686
        },
        "selected": true,
        "name": "图文选单 B",
        "chatBarText": "查看更多信息",
        "areas": [
            {
                "bounds": { "x": 0, "y": 0, "width": 833, "height": 843 },
                "action": {
                    "type": "richmenuswitch",
                    "richMenuAliasId": "richmenu_a",
                    "data": "richmenu-changed-to-a"
                }
            },
            {
                "bounds": { "x": 834, "y": 0, "width": 833, "height": 843 },
                "action": { "type": "message", "text": "B" }
            }
        ]
    }"""

    # 创建图文选单 A
    rich_menu_a_id = create_rich_menu(api_client, rich_menu_a_str, 'static/1.png', 'richmenu_a')

    # 设置默认图文选单
    line_bot_api = MessagingApi(api_client)
    line_bot_api.set_default_rich_menu(rich_menu_a_id)

    # 创建图文选单 B
    create_rich_menu(api_client, rich_menu_b_str, 'static/2.png', 'richmenu_b')
