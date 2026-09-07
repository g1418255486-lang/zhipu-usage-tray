import requests
from datetime import datetime
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


PLATFORMS = {
    "zhipu": {
        "name": "智谱 (open.bigmodel.cn)",
        "base_url": "https://open.bigmodel.cn",
    },
    "zai": {
        "name": "Z.ai (api.z.ai)",
        "base_url": "https://api.z.ai",
    },
}


class UsageData:
    def __init__(self):
        self.token_percentage: Optional[float] = None
        self.mcp_percentage: Optional[float] = None
        self.mcp_current_usage: Optional[str] = None
        self.mcp_total: Optional[str] = None
        self.mcp_details: Optional[list] = None
        self.model_usage: Optional[dict] = None
        self.tool_usage: Optional[dict] = None
        self.error: Optional[str] = None
        self.platform: Optional[str] = None
        self.raw_quota: Optional[dict] = None
        self.raw_model: Optional[dict] = None
        self.raw_tool: Optional[dict] = None
        self.token_5h: Optional[int] = None
        self.call_5h: Optional[int] = None
        self.token_5h_pct: Optional[float] = None
        self.token_weekly_pct: Optional[float] = None
        self.token_5h_reset: Optional[int] = None
        self.token_weekly_reset: Optional[int] = None


class APIClient:
    def __init__(self, api_key: str, platform_key: str = "zhipu"):
        self.api_key = api_key
        self.platform_key = platform_key
        self.platform_info = PLATFORMS.get(platform_key, PLATFORMS["zhipu"])
        self.base_url = self.platform_info["base_url"]

        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=1,
                      status_forcelist=[429, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def _get_headers(self):
        return {
            "Authorization": self.api_key,
            "Accept-Language": "zh-CN,zh",
            "Content-Type": "application/json",
        }

    def _time_window(self):
        from datetime import timedelta
        now = datetime.now()
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        start = (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        return start, end

    def _query(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def fetch_all(self) -> UsageData:
        data = UsageData()
        data.platform = self.platform_info["name"]

        try:
            start, end = self._time_window()
            time_params = {"startTime": start, "endTime": end}

            data.raw_model = self._query("/api/monitor/usage/model-usage", time_params)
            data.model_usage = data.raw_model.get("data", data.raw_model)

            if data.model_usage:
                total = data.model_usage.get("totalUsage")
                if isinstance(total, dict):
                    data.token_5h = total.get("totalTokensUsage")
                    data.call_5h = total.get("totalModelCallCount")
        except Exception as e:
            data.error = f"模型用量查询失败: {e}"
            return data

        try:
            data.raw_tool = self._query("/api/monitor/usage/tool-usage", time_params)
            data.tool_usage = data.raw_tool.get("data", data.raw_tool)
        except Exception as e:
            if not data.error:
                data.error = f"工具用量查询失败: {e}"

        try:
            data.raw_quota = self._query("/api/monitor/usage/quota/limit")
            quota = data.raw_quota.get("data", data.raw_quota)
            if quota and "limits" in quota:
                for item in quota["limits"]:
                    if item.get("type") == "TOKENS_LIMIT":
                        unit = item.get("unit")
                        pct = item.get("percentage")
                        reset_ts = item.get("nextResetTime")
                        if unit == 3:
                            data.token_5h_pct = pct
                            data.token_5h_reset = reset_ts
                        elif unit == 6:
                            data.token_weekly_pct = pct
                            data.token_weekly_reset = reset_ts
                        data.token_percentage = pct
                    elif item.get("type") == "TIME_LIMIT":
                        data.mcp_percentage = item.get("percentage")
                        data.mcp_current_usage = item.get("currentValue")
                        data.mcp_total = item.get("usage")
                        data.mcp_details = item.get("usageDetails")
        except Exception as e:
            if not data.error:
                data.error = f"配额查询失败: {e}"

        return data
