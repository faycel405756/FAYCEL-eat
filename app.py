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

            # 1) إرسال Eat Token إلى Garena
            url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
            res = await client.get(url)

            # لازم يكون Redirect
            if not (300 <= res.status_code < 400):
                return {"error": "Invalid or expired eat token"}

            location = res.headers.get("Location")
            if not location:
                return {"error": "No redirect location"}

            # 2) استخراج البيانات من رابط التحويل
            parsed = urlparse(location)
            params = parse_qs(parsed.query)

            access_token = params.get("access_token", [None])[0]
            account_id = params.get("account_id", [None])[0]
            nickname = params.get("nickname", [None])[0]
            region = params.get("region", [None])[0]
            game = params.get("game", [None])[0]
            lang = params.get("lang", [None])[0]

            if not access_token or not account_id:
                return {"error": "Failed to extract data from redirect"}

            # 3) إرجاع نفس البيانات كـ JSON
            return {
                "status": "success",
                "access_token": access_token,
                "account_id": account_id,
                "nickname": nickname,
                "region": region,
                "game": game,
                "lang": lang,
                "redirect_url": location
            }

    except Exception as e:
        return {"error": "server error", "details": str(e)}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <center>
        <h2>Garena Eat Token Decoder</h2>
        <p>Use:</p>
        <code>/Eat?eat_token=YOUR_EAT_TOKEN</code>
    </center>
    """


@app.get("/Eat")
async def eat(eat_token: str = Query(..., description="Garena Eat Token")):
    return await get_garena_data(eat_token)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)
