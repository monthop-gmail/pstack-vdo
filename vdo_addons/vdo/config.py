from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class VdoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PSTACK_VDO_", env_file=".env", extra="ignore")

    hls_dir: str = "hls"        # PSTACK_VDO_HLS_DIR — โฟลเดอร์เก็บ playlist/segment
    ffmpeg_bin: str = "ffmpeg"  # PSTACK_VDO_FFMPEG_BIN
    segment_seconds: int = 6


@lru_cache
def get_vdo_settings() -> VdoSettings:
    return VdoSettings()
