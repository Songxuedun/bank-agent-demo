import secrets
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。密钥只从环境变量 / .env 读取，代码里不放默认值。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # DeepSeek API (在 backend/.env 里配置 DEEPSEEK_API_KEY)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 服务配置
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/bank_assistant.db"

    # 登录令牌: 未配置 TOKEN_SECRET 时每次启动随机生成(重启后需重新登录)
    token_secret: str = Field(default_factory=lambda: secrets.token_hex(32))
    token_ttl_seconds: int = 60 * 60 * 8

    # 安全配置
    mfa_code: str = "123456"  # 演示用静态验证码，真实环境应换成短信/TOTP
    daily_transfer_limit: float = 1000.0  # 黄色权限单笔/日累计阈值


settings = Settings()
