import os
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import requests

logging.basicConfig(level=logging.INFO)
logging.info("Баха ёрдамчи запускается")

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")

BASE_URL = "https://platform-api.max.ru"


def api_request(method, endpoint, **kwargs):
    headers = {"Authorization": TOKEN}
    response = requests.request(
        method,
        f"{BASE_URL}{endpoint}",
        headers=headers,
        timeout=20,
        **kwargs,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def send_message(chat_id, text):
    return api_request(
        "POST",
        "/messages",
        params={"chat_id": chat_id},
        json={"text": text},
    )


def process_updates():
    marker = None

    while True:
        try:
            params = {"timeout": 30}
            if marker is not None:
                params["marker"] = marker

            data = api_request("GET", "/updates", params=params)

            if "marker" in data:
                marker = data["marker"]

            for update in data.get("updates", []):
                try:
                    update_type = update.get("update_type")

                    if update_type == "message_created":
                        message = update.get("message", {})
                        body = message.get("body", {})
                        text = body.get("text", "").strip()

                        chat_id = (
                            message.get("recipient", {}).get("chat_id")
                            or update.get("chat_id")
                        )

                        if not chat_id:
                            continue

                        if text.lower() in ("/start", "/start@baha_yordamchi"):
                            send_message(
                                chat_id,
                                "Ассалому алайкум! Мен — Баха ёрдамчи 🤖\n"
                                "Гуруҳга хуш келибсиз!\n"
                                "/help — ёрдам",
                            )

                        elif text.lower() in ("/help", "/help@baha_yordamchi"):
                            send_message(
                                chat_id,
                                "📋 Баха ёрдамчи буйруқлари:\n"
                                "/start — ботни бошлаш\n"
                                "/help — ёрдам",
                            )

                except Exception:
                    logging.exception("Хабарни қайта ишлашда хатолик")

        except Exception:
            logging.exception("MAX API билан боғланишда хатолик")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Baha yordamchi ishlayapti".encode())

    def log_message(self, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    Thread(target=start_health_server, daemon=True).start()
    process_updates()
