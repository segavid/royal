from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error
import re

TARGET_SOURCE_DOMAIN = 'w.royal-drama.com'
VERIFICATION_TAG = '<meta name="google-site-verification" content="4aeE1nom200vJpqjv46jujHDGVAuIdF2tA8rycTjFnE" />'

BANNER_HTML = '''<br><br><br><div style="margin:32px auto 24px auto;max-width:900px;border:2px solid #d32f2f;border-radius:15px;background:#fafafa;padding:16px 10px;text-align:center;font-family:'Tajawal',Arial,sans-serif;font-size:24px;color:#d32f2f;font-weight:bold;box-shadow:0 2px 8px #0001;">
  <a title="قصة عشق" href="https://z.3isk.news/video/" style="color:#d32f2f;text-decoration:none;">قصة عشق</a>
  <span style="font-weight:normal;color:#d32f2f;margin:0 16px;">-</span>
  <a title="مسلسل حلم أشرف" href="https://z.3isk.news/series/3isk-se-esref-ruya-watch/" style="color:#d32f2f;text-decoration:none;">مسلسل حلم أشرف</a>
  <span style="font-weight:normal;color:#d32f2f;margin:0 16px;">-</span>
  <a title="مسلسل المدينة البعيدة" href="https://z.3isk.news/series/3isk-se-uzak-sehir-watch-esh-1i30h/" style="color:#d32f2f;text-decoration:none;">مسلسل المدينة البعيدة</a>
</div>'''

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            path = self.path
            if path.startswith('/api'):
                path = path[4:] or '/'

            # ✅ Serve Google verification file directly
            if path == "/googlec592fabc25eec3b8.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"google-site-verification: googlec592fabc25eec3b8.html")
                return

            target_url = f"https://{TARGET_SOURCE_DOMAIN}{path}"

            host = self.headers.get('host', 'localhost')
            proto = self.headers.get('x-forwarded-proto', 'https')
            worker_origin = f"{proto}://{host}"

            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "*/*"
                }
            )

            try:
                response = urllib.request.urlopen(req, timeout=10)
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error {e.code}".encode())
                return

            content_type = response.headers.get("Content-Type", "").lower()
            body = response.read()

            # ✅ Handle HTML
            if "text/html" in content_type:
                html = body.decode("utf-8", errors="ignore")

                html = re.sub(f"https://{TARGET_SOURCE_DOMAIN}", worker_origin, html, flags=re.IGNORECASE)
                html = re.sub(f"http://{TARGET_SOURCE_DOMAIN}", worker_origin, html, flags=re.IGNORECASE)
                html = re.sub(f"//{TARGET_SOURCE_DOMAIN}", f"//{host}", html, flags=re.IGNORECASE)

                html = re.sub(r'<script[^>]*googletagmanager[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'<script[^>]*gtag[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'<script[^>]*revenuecpmgate[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'<script[^>]*cloudflareinsights[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'<script[^>]*aclib[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'aclib\.runAutoTag.*?;', '', html, flags=re.DOTALL | re.IGNORECASE)

                html = re.sub(
                    r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex[^"\']*["\'][^>]*>',
                    '<meta name="robots" content="index, follow">',
                    html,
                    flags=re.IGNORECASE
                )
                html = re.sub(r'<meta[^>]*name=["\']googlebot["\'][^>]*>', '', html, flags=re.IGNORECASE)

                html = html.replace('watch.php', 'view.php').replace('WATCH.PHP', 'view.php')

                html = re.sub(r'(<head[^>]*>)', rf'\1\n{VERIFICATION_TAG}\n', html, count=1, flags=re.IGNORECASE)
                html = re.sub(r'(<body[^>]*>)', rf'\1\n{BANNER_HTML}', html, count=1, flags=re.IGNORECASE)

                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=UTF-8')
                self.send_header('X-Robots-Tag', 'index, follow')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
                return

            # ✅ Handle XML
            if any(x in content_type for x in ['xml', 'rss']) or path.endswith('.xml'):
                text = body.decode("utf-8", errors="ignore")
                text = re.sub(f"https://{TARGET_SOURCE_DOMAIN}", worker_origin, text, flags=re.IGNORECASE)

                self.send_response(200)
                self.send_header('Content-Type', 'application/xml; charset=UTF-8')
                self.end_headers()
                self.wfile.write(text.encode('utf-8'))
                return

            # ✅ Binary files (images, css, js, etc.)
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
