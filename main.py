import os
import json
import re
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from astrbot.api.all import *
from astrbot.api.event import filter

class SpotifyController(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.sp = None
        self.auth_manager = None
        # 初始化时加载一次配置
        self._load_config_and_init()

    def _load_config_and_init(self):
        """核心逻辑：从插件目录实时加载 WebUI 保存的配置"""
        config = {}
        
        # WebUI 保存的配置存放在当前代码同目录下
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass
                
        # 加个 .strip()，防止在 WebUI 复制粘贴时不小心多带了空格
        client_id = config.get("client_id", "").strip()
        client_secret = config.get("client_secret", "").strip()
        redirect_uri = config.get("redirect_uri", "http://127.0.0.1:6198/callback").strip()
        
        # 终极防呆：强制提取纯净的 URL，过滤掉可能的 Markdown 括号
        if "[" in redirect_uri or "]" in redirect_uri:
            match = re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', redirect_uri)
            if match:
                redirect_uri = match.group(0)
        
        # 如果读取到的还是未修改的占位符或者为空，直接挂起等待配置
        if not client_id or not client_secret or client_id == "你的_CLIENT_ID" or client_id == "YOUR_SPOTIFY_CLIENT_ID":
            return
            
        scope = "user-modify-playback-state user-read-playback-state user-library-modify"
        
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            open_browser=False 
        )
        
        token_info = self.auth_manager.validate_token(self.auth_manager.cache_handler.get_cached_token())
        if token_info:
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
        else:
            self.sp = None

    # ================= 供人类用户使用的授权指令 =================

    @filter.command("spotify登录")
    async def spotify_login(self, event: AstrMessageEvent):
        """生成授权链接发给用户"""
        # 生成链接前重新加载配置，确保读取的是 WebUI 中最新保存的值
        self._load_config_and_init()
        
        if
