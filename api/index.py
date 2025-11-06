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

            # Determine current worker domain
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
                # Handle 404 redirect
                if e.code == 404:
                    self.send_response(302)
                    self.send_header('Location', worker_origin + '/')
                    self.end_headers()
                    return
                else:
                    self.send_response(e.code)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error {e.code}'.encode())
                    return

            content_type = response.headers.get('Content-Type', '').lower()
            body = response.read()

            # ---- Non-HTML files (CSS, JS, images, etc.)
            if 'text/html' not in content_type:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(body)
                return

            # ---- HTML processing
            html = body.decode('utf-8', errors='ignore')

            # Rewrite all absolute & relative URLs to worker domain
            html = re.sub(r'https://www\.zamanarabic\.com', worker_origin, html, flags=re.IGNORECASE)
            html = re.sub(r'href="/', f'href="{worker_origin}/', html)
            html = re.sub(r'src="/', f'src="{worker_origin}/', html)

            # Inject custom <li> links into nav
            html = re.sub(
                r'(<div class="jeg_nav_item">\s*<ul[^>]*class="jeg_menu jeg_top_menu"[^>]*>)([\s\S]*?)(<\/ul>)',
                rf'\1\2{CUSTOM_LINKS}\3',
                html,
                flags=re.IGNORECASE
            )

            # Return final modified HTML
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=UTF-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'Error: {e}'.encode('utf-8'))
