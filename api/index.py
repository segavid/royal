from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error
import re

TARGET_SOURCE_DOMAIN = 'w.royal-drama.com'
VERIFICATION_TAG = '<meta name="google-site-verification" content="4aeE1nom200vJpqjv46jujHDGVAuIdF2tA8rycTjFnE" />'

BANNER_HTML = '''<br><br><div style="margin:40px auto;max-width:900px;border:2px solid #ff004c;border-radius:14px;background:linear-gradient(135deg,#fff 0%,#ffe6eb 100%);padding:18px 12px;text-align:center;font-family:'Tajawal',Arial,sans-serif;font-size:22px;color:#b30032;font-weight:bold;box-shadow:0 3px 10px rgba(0,0,0,0.1);line-height:1.8;">
  <a title="مسلسلات تركية" href="https://z.3isk.news/all-turkish-series-esheeq/" style="color:#b30032;text-decoration:none;padding:0 10px;">مسلسلات تركية</a>
  <span style="font-weight:normal;color:#b30032;">•</span>
  <a title="مسلسل حلم اشرف" href="https://z.3isk.news/series/3isk-se-esref-ruya-watch/" style="color:#b30032;text-decoration:none;padding:0 10px;">مسلسل حلم اشرف</a>
  <span style="font-weight:normal;color:#b30032;">•</span>
  <a title="مسلسل المدينة البعيدة" href="https://z.3isk.news/series/3isk-se-uzak-sehir-watch-esh-1i30h/" style="color:#b30032;text-decoration:none;padding:0 10px;">مسلسل المدينة البعيدة</a>
  <span style="font-weight:normal;color:#b30032;">•</span>
  <a title="موقع عشق الاصلي" href="https://z.3isk.news/series/3isk-se-uzak-sehir-watch-esh-1i30h/" style="color:#b30032;text-decoration:none;padding:0 10px;">موقع عشق الاصلي</a>
</div>'''


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get path
            path = self.path
            if path.startswith('/api'):
                path = path[4:] or '/'
            
            target_url = f"https://{TARGET_SOURCE_DOMAIN}{path}"
            
            # Get worker domain
            host = self.headers.get('host', 'localhost')
            proto = self.headers.get('x-forwarded-proto', 'https')
            worker_origin = f"{proto}://{host}"
            
            # Make request
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
            
            # Handle HTML
            if "text/html" in content_type:
                html = body.decode("utf-8", errors="ignore")
                
                # Replace domain
                html = re.sub(
                    f"https://{TARGET_SOURCE_DOMAIN}",
                    worker_origin,
                    html,
                    flags=re.IGNORECASE
                )
                html = re.sub(
                    f"http://{TARGET_SOURCE_DOMAIN}",
                    worker_origin,
                    html,
                    flags=re.IGNORECASE
                )
                html = re.sub(
                    f"//{TARGET_SOURCE_DOMAIN}",
                    f"//{host}",
                    html,
                    flags=re.IGNORECASE
                )
                
                # Remove ads
                html = re.sub(r'<script[^>]*googletagmanager[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = re.sub(r'<script[^>]*gtag[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = re.sub(r'<script[^>]*revenuecpmgate[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = re.sub(r'<script[^>]*cloudflareinsights[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = re.sub(r'<script[^>]*aclib[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = re.sub(r'aclib\.runAutoTag.*?;', '', html, flags=re.DOTALL|re.IGNORECASE)
                
                # Fix robots
                html = re.sub(
                    r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex[^"\']*["\'][^>]*>',
                    '<meta name="robots" content="index, follow">',
                    html,
                    flags=re.IGNORECASE
                )
                html = re.sub(
                    r'<meta[^>]*name=["\']googlebot["\'][^>]*>',
                    '',
                    html,
                    flags=re.IGNORECASE
                )
                
                # Replace watch.php
                html = html.replace('watch.php', 'view.php')
                html = html.replace('WATCH.PHP', 'view.php')
                
                # Inject in head
                html = re.sub(
                    r'(<head[^>]*>)',
                    rf'\1\n{VERIFICATION_TAG}\n',
                    html,
                    count=1,
                    flags=re.IGNORECASE
                )
                
                # Inject banner
                html = re.sub(
                    r'(<body[^>]*>)',
                    rf'\1\n{BANNER_HTML}',
                    html,
                    count=1,
                    flags=re.IGNORECASE
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=UTF-8')
                self.send_header('X-Robots-Tag', 'index, follow')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
                return
            
            # Handle XML
            if any(x in content_type for x in ['xml', 'rss']) or path.endswith('.xml'):
                text = body.decode("utf-8", errors="ignore")
                text = re.sub(
                    f"https://{TARGET_SOURCE_DOMAIN}",
                    worker_origin,
                    text,
                    flags=re.IGNORECASE
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/xml; charset=UTF-8')
                self.end_headers()
                self.wfile.write(text.encode('utf-8'))
                return
            
            # Binary files
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(body)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            error_msg = f"Error: {str(e)}"

            self.wfile.write(error_msg.encode())

