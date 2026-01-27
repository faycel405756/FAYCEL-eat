import httpx
import warnings
from fastapi import FastAPI, Query
from urllib.parse import urlparse, parse_qs
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

app = FastAPI(title="Garena Eat Token Decoder API")


@app.get("/decode")
async def decode_eat_token(
    eat_token: str = Query(..., description="Garena Eat Token")
):
    try:
        async with httpx.AsyncClient(
            verify=False,
            timeout=10.0,
            follow_redirects=False
        ) as client:

            # إرسال التوكن إلى Garena
            url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
            response = await client.get(url)

            if not (300 <= response.status_code < 400):
                return {
                    "status": "error",
                    "message": "Invalid or expired eat token"
                }

            location = response.headers.get("Location")
            if not location:
                return {
                    "status": "error",
                    "message": "Redirect location not found"
                }

            # استخراج البيانات من رابط التحويل
            parsed = urlparse(location)
            params = parse_qs(parsed.query)

            access_token = params.get("access_token", [None])[0]
            account_id = params.get("account_id", [None])[0]
            nickname = params.get("nickname", [None])[0]
            region = params.get("region", [None])[0]
            game = params.get("game", [None])[0]
            lang = params.get("lang", [None])[0]

            if not access_token or not account_id:
                return {
                    "status": "error",
                    "message": "Failed to extract redirect data"
                }

            return {
                "status": "success",
                "access_token": access_token,
                "account_id": account_id,
                "nickname": nickname,
                "region": region,
                "game": game,
                "language": lang,
                "redirect_url": location
            }

    except Exception as e:
        return {
            "status": "error",
            "message": "Server error",
            "details": str(e)
        }


@app.get("/")
def home():
    return {
        "message": "Garena Eat Token Decoder API",
        "usage": "/decode?eat_token=YOUR_EAT_TOKEN"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)
