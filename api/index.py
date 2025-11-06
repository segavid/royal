from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error
import re

TARGET_SOURCE_DOMAIN = 'www.zamanarabic.com'

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
            if path.startswith('/api'):
                path = path[4:] or '/'

            # Build target URL
            target_url = f'https://{TARGET_SOURCE_DOMAIN}{path}'

            # Worker origin
            host = self.headers.get('host', 'localhost')
            proto = self.headers.get('x-forwarded-proto', 'https')
            worker_origin = f'{proto}://{host}'

            # Fetch target
            req = urllib.request.Request(
                target_url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; CloudflareWorker/1.0)'}
            )

            try:
                response = urllib.request.urlopen(req, timeout=15)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.send_response(302)
                    self.send_header('Location', worker_origin + '/')
                    self.end_headers()
                    return
                self.send_response(e.code)
                self.end_headers()
                self.wfile.write(f'Error {e.code}'.encode())
                return

            content_type = response.headers.get('Content-Type', '').lower()
            body = response.read()

            # 🧩 Serve non-HTML files directly from origin
            if not content_type.startswith('text/html'):
                self.send_response(302)
                self.send_header('Location', f'https://{TARGET_SOURCE_DOMAIN}{path}')
                self.end_headers()
                return

            # 🧠 Process HTML
            html = body.decode('utf-8', errors='ignore')

            # Fix asset URLs (CSS/JS/images) to load from origin
            html = re.sub(r'href="/([^"]+\.(?:css|js|png|jpg|jpeg|gif|webp|svg|ico))"',
                          rf'href="https://{TARGET_SOURCE_DOMAIN}/\1"', html)
            html = re.sub(r'src="/([^"]+\.(?:css|js|png|jpg|jpeg|gif|webp|svg|ico))"',
                          rf'src="https://{TARGET_SOURCE_DOMAIN}/\1"', html)

            # Rewrite other internal links to worker domain
            html = re.sub(r'https://www\.zamanarabic\.com', worker_origin, html, flags=re.IGNORECASE)
            html = re.sub(r'href="/', f'href="{worker_origin}/', html)
            html = re.sub(r'src="/', f'src="{worker_origin}/', html)

            # Inject custom links into navigation
            html = re.sub(
                r'(<div class="jeg_nav_item">\s*<ul[^>]*class="jeg_menu jeg_top_menu"[^>]*>)([\s\S]*?)(<\/ul>)',
                rf'\1\2{CUSTOM_LINKS}\3',
                html,
                flags=re.IGNORECASE
            )

            # Send final response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=UTF-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'Error: {e}'.encode('utf-8'))
