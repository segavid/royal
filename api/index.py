from http.server import BaseHTTPRequestHandler
import urllib.request
import re

# === CONFIG ===
TARGET_SOURCE_DOMAIN = 'w.royal-drama.com'
VERIFICATION_TAG = '<meta name="google-site-verification" content="HWrhtgkCPV2OT-OWRzV60Vdl1pWxt35-aEZ7NNDTHWs" />'

BANNER_HTML = '''<br><br><br><div style="margin:32px auto 24px auto;max-width:900px;border:2px solid #d32f2f;border-radius:15px;background:#fafafa;padding:16px 10px;text-align:center;font-family:'Tajawal',Arial,sans-serif;font-size:24px;color:#d32f2f;font-weight:bold;box-shadow:0 2px 8px #0001;">
  <a title="قصة عشق" href="https://z.3isk.news/video/" style="color:#d32f2f;text-decoration:none;">قصة عشق</a>
  <span style="font-weight:normal;color:#d32f2f;margin:0 16px;">-</span>
  <a href="https://z.3isk.news/series/3isk-se-esref-ruya-watch/" style="color:#d32f2f;text-decoration:none;">مسلسل حلم اشرف</a>
  <span style="font-weight:normal;color:#d32f2f;margin:0 16px;">-</span>
  <a href="https://z.3isk.news/series/3isk-se-uzak-sehir-watch-esh-1i30h/" style="color:#d32f2f;text-decoration:none;">مسلسل المدينه البعيده</a>
</div>'''

def escape_regex(s):
    """Escape special regex characters"""
    return re.escape(s)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_HEAD(self):
        self.handle_request()

    def handle_request(self):
        try:
            # Parse request
            path = self.path.split('?')[0]
            query = self.path.split('?')[1] if '?' in self.path else ""
            
            # Remove /api prefix if present
            if path.startswith('/api'):
                path = path[4:] or '/'
            
            full_query = f"?{query}" if query else ""
            target_url = f"https://{TARGET_SOURCE_DOMAIN}{path}{full_query}"
            
            # Get worker domain
            host = self.headers.get('host', 'localhost')
            proto = self.headers.get('x-forwarded-proto', 'https')
            worker_origin = f"{proto}://{host}"
            
            # Create domain regex pattern
            domain_pattern = re.compile(
                f"(https?:)?//{escape_regex(TARGET_SOURCE_DOMAIN)}", 
                re.IGNORECASE
            )
            
            print(f"Target URL: {target_url}")
            
            # Make request to target
            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": f"https://{TARGET_SOURCE_DOMAIN}/"
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                body = response.read()
                
                # === Handle HTML ===
                if "text/html" in content_type:
                    html = body.decode("utf-8", errors="ignore")
                    
                    # Remove Google Analytics
                    html = re.sub(
                        r'<!--\s*Google tag \(gtag\.js\)\s*-->[\s\S]*?<script async src=["\']https://www\.googletagmanager\.com/gtag/js\?id=[^"\']+["\']></script>[\s\S]*?<script>[\s\S]*?gtag\([^)]*\);[\s\S]*?</script>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    # Remove ad scripts
                    html = re.sub(
                        r'<script[^>]*src=["\']//pl26380627\.revenuecpmgate\.com/[^"\']+["\'][^>]*></script>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    html = re.sub(
                        r'<script>\(function\(\)\{function c\(\)\{var b=a\.contentDocument[\s\S]*?\}\)\(\);</script>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    html = re.sub(
                        r'<script[^>]*src=["\']https://static\.cloudflareinsights\.com/beacon\.min\.js[^"\']*["\'][^>]*data-cf-beacon[^>]*></script>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    # Remove aclib scripts
                    html = re.sub(
                        r'aclib\.runAutoTag\s*\(\s*\{[\s\S]*?\}\s*\)\s*;?',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    html = re.sub(
                        r'<script[^>]*\bid=["\']?aclib["\']?[^>]*src=["\'](?:https?:)?//acscdn\.com/script/aclib\.js["\'][^>]*></script>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    html = re.sub(
                        r'<script[^>]*src=["\'](?:https?:)?//acscdn\.com/script/aclib\.js["\'][^>]*></script>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    # Fix noindex meta tags
                    html = re.sub(
                        r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex[^"\']*["\']\s*/?>',
                        '<meta name="robots" content="index, follow">',
                        html, flags=re.IGNORECASE
                    )
                    
                    html = re.sub(
                        r'<meta\s+content=["\'][^"\']*noindex[^"\']*["\']\s+name=["\']robots["\']\s*/?>',
                        '<meta name="robots" content="index, follow">',
                        html, flags=re.IGNORECASE
                    )
                    
                    # Remove googlebot noindex
                    html = re.sub(
                        r'<meta\s+name=["\']googlebot["\']\s+content=["\'][^"\']*noindex[^"\']*["\']\s*/?>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    html = re.sub(
                        r'<meta\s+content=["\'][^"\']*noindex[^"\']*["\']\s+name=["\']googlebot["\']\s*/?>',
                        '', html, flags=re.IGNORECASE
                    )
                    
                    # Replace domain references
                    html = domain_pattern.sub(worker_origin, html)
                    
                    # Replace watch.php with view.php
                    html = re.sub(r'watch\.php', 'view.php', html, flags=re.IGNORECASE)
                    
                    # Inject verification tag in head
                    html = re.sub(
                        r'<head[^>]*>',
                        lambda m: f"{m.group(0)}\n{VERIFICATION_TAG}\n",
                        html, count=1, flags=re.IGNORECASE
                    )
                    
                    # Inject banner after body tag
                    html = re.sub(
                        r'<body[^>]*>',
                        lambda m: f"{m.group(0)}\n{BANNER_HTML}",
                        html, count=1, flags=re.IGNORECASE
                    )
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=UTF-8')
                    self.send_header('X-Robots-Tag', 'index, follow')
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))
                    return
                
                # === Handle XML/RSS ===
                looks_xml = re.search(r'\.xml($|\?)', path, re.IGNORECASE)
                if any(x in content_type for x in ["xml", "rss", "text/plain"]) or looks_xml:
                    text = body.decode("utf-8", errors="ignore")
                    text = domain_pattern.sub(worker_origin, text)
                    
                    mime = 'application/xml; charset=UTF-8' if (looks_xml or 'xml' in content_type or 'rss' in content_type) else 'text/plain; charset=UTF-8'
                    
                    self.send_response(200)
                    self.send_header('Content-Type', mime)
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.end_headers()
                    self.wfile.write(text.encode('utf-8'))
                    return
                
                # === Handle Binary (images, CSS, JS, etc) ===
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Cache-Control', 'public, max-age=31536000')
                self.end_headers()
                self.wfile.write(body)
                return
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
            return