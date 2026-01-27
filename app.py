import httpx
import warnings
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from urllib.parse import urlparse, parse_qs
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

app = FastAPI()

async def get_garena_data(eat_token: str):
    try:
        async with httpx.AsyncClient(
            verify=False,
            timeout=10.0,
            follow_redirects=False
        ) as client:

            # ===== Garena Callback =====
            callback_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
            response = await client.get(callback_url)

            if not (300 <= response.status_code < 400):
                return {"error": "Invalid access token or expired"}

            redirect_url = response.headers.get("Location")
            if not redirect_url:
                return {"error": "Redirect location missing"}

            parsed_url = urlparse(redirect_url)
            params = parse_qs(parsed_url.query)

            token_value = params.get("access_token", [None])[0]
            account_id = params.get("account_id", [None])[0]
            account_nickname = params.get("nickname", [None])[0]
            region = params.get("region", [None])[0]

            if not token_value or not account_id:
                return {"error": "Failed to extract Garena data"}

            # ===== topup.pk request (unchanged) =====
            openid_url = "https://topup.pk/api/auth/player_id_login"

            openid_headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-MM,en-US;q=0.9,en;q=0.8",
                "Content-Type": "application/json",
                "Origin": "https://topup.pk",
                "Referer": "https://topup.pk/",
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Android WebView";v="138"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Linux; Android 15; RMX5070 Build/UKQ1.231108.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.157 Mobile Safari/537.36",
                "X-Requested-With": "mark.via.gp",
                "Cookie": "source=mb; region=PK; mspid2=13c49fb51ece78886ebf7108a4907756; _fbp=fb.1.1753985808817.794945392376454660; language=en; datadome=WQaG3HalUB3PsGoSXY3TdcrSQextsSFwkOp1cqZtJ7Ax4YkiERHUgkgHlEAIccQO~w8dzTGM70D9SzaH7vymmEqOrVeX5pIsPVE22Uf3TDu6W3WG7j36ulnTg2DltRO7; session_key=hq02g63z3zjcumm76mafcooitj7nc79y",
            }

            payload = {
                "app_id": 100067,
                "login_id": str(account_id)
            }

            openid_res = await client.post(
                openid_url,
                headers=openid_headers,
                json=payload
            )

            if openid_res.status_code != 200:
                return {"error": "topup.pk request failed"}

            try:
                openid_data = openid_res.json()
            except Exception:
                return {"error": "Invalid JSON from topup.pk"}

            open_id = openid_data.get("open_id")
            if not open_id:
                return {"error": "open_id not found"}

            return {
                "status": "success",
                "account_id": account_id,
                "account_nickname": account_nickname,
                "open_id": open_id,
                "access_token": token_value,
                "region": region,
                "credit": "INSTAGRAM : @bxl2_8",
                "Power By": "تفو  : عليك"
            }

    except Exception as e:
        return {"error": "Server error", "details": str(e)}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <div style="text-align:center">
        <h1>Eat Token Decoder API Running</h1>
        <p>/Eat?eat_token=TOKEN</p>
    </div>
    """


@app.get("/Eat")
async def get_token_info(
    eat_token: str = Query(..., description="Garena Access Token")
):
    return await get_garena_data(eat_token)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)
