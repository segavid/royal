from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error
import re

TARGET_SOURCE_DOMAIN = "www.zamanarabic.com"

CUSTOM_LINKS = '''
<li class="page_item"><a title="قصة عشق" href="https://z.3isk.news/">قصة عشق</a></li>
<li class="page_item"><a href="https://z.3isk.news/series/3isk-se-esref-ruya-watch-esh-tvmua/">مسلسل حلم اشرف</a></li>
<li class="page_item"><a href="https://z.3isk.news/series/3isk-se-tasacak-bu-deniz-watch/">مسلسل هذا البحر سوف يفيض</a></li>
<li class="page_item"><a href="https://z.3isk.news/series/3isk-se-uzak-sehir-watch-esh-zwoc1/">مسلسل المدينة البعيدة</a></li>
'''

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            path = self.path
            if path.startswith("/api"):
                path = path[4:] or "/"

            # full URL on origin
            target_url = f"https://{TARGET_SOURCE_DOMAIN}{path}"

            host = self.headers.get("host", "localhost")
            proto = self.headers.get("x-forwarded-proto", "https")
            worker_origin = f"{proto}://{host}"

            # --- Always let CSS, JS, image and static files load directly from origin ---
            if re.search(r'\.(css|js|jpg|jpeg|png|gif|svg|ico|webp|woff2?|ttf|eot|mp4|json)(\?|$)', path, re.IGNORECASE):
                self.send_response(302)
                self.send_header("Location", f"https://{TARGET_SOURCE_DOMAIN}{path}")
                self.end_headers()
                return

            # fetch HTML or dynamic page
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; CloudflareWorker/1.0)"}
            )

            try:
                response = urllib.request.urlopen(req, timeout=15)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.send_response(302)
                    self.send_header("Location", worker_origin + "/")
                    self.end_headers()
                    return
                self.send_response(e.code)
                self.end_headers()
                self.wfile.write(f"Error {e.code}".encode())
                return

            content_type = response.headers.get("Content-Type", "").lower()
            body = response.read()

            # --- Non-HTML (e.g., XML, RSS): serve directly ---
            if "text/html" not in content_type:
                self.send_response(302)
                self.send_header("Location", f"https://{TARGET_SOURCE_DOMAIN}{path}")
                self.end_headers()
                return

            # --- HTML ---
            html = body.decode("utf-8", errors="ignore")

            # Fix all asset URLs to original domain
            html = re.sub(r'href="(/[^"]+\.(?:css|js|png|jpg|jpeg|gif|webp|svg|ico|woff2?|ttf|eot))"',
                          rf'href="https://{TARGET_SOURCE_DOMAIN}\1"', html)
            html = re.sub(r'src="(/[^"]+\.(?:css|js|png|jpg|jpeg|gif|webp|svg|ico|woff2?|ttf|eot|mp4))"',
                          rf'src="https://{TARGET_SOURCE_DOMAIN}\1"', html)

            # Replace absolute domain references for HTML links
            html = re.sub(r'https://www\.zamanarabic\.com', worker_origin, html, flags=re.IGNORECASE)
            html = re.sub(r'href="/', f'href="{worker_origin}/', html)
            html = re.sub(r'src="/', f'src="{worker_origin}/', html)

            # Inject custom <li> links into menu
            html = re.sub(
                r'(<div class="jeg_nav_item">\s*<ul[^>]*class="jeg_menu jeg_top_menu"[^>]*>)([\s\S]*?)(<\/ul>)',
                rf'\1\2{CUSTOM_LINKS}\3',
                html,
                flags=re.IGNORECASE
            )

            # Return modified HTML
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=UTF-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode("utf-8"))
