"""Same-origin, loopback-only workbench. Run: python -m workbench.api."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from source_adapters.corpus import build_source_packet, list_procedures
from workbench.presentation import ontology_reference
from source_adapters.dependencies import validate as validate_artifacts
from workbench.service import (analyze_procedure, apply_adjudication_decision,
                               branch_adjudication, compile_adjudication,
                               compile_procedure, execute_adjudication, open_adjudication)

MAX_BODY = 262144


def make_server(root, port=8789, site_root=None):
    root = Path(root).resolve()
    site_root = Path(site_root or root / '.cache/workbench/site').resolve()
    if root.is_relative_to(site_root) or not (site_root / 'adjudication/index.html').is_file():
        raise ValueError('site_build_missing: build Eleventy into .cache/workbench/site first')
    page = (site_root / 'adjudication/index.html').read_text(encoding='utf-8')
    prefix = re.search(r'''<html\b[^>]*\bdata-baseurl\s*=\s*["']([^"']+)["']''', page, re.IGNORECASE)
    if prefix and prefix[1] != '/':
        raise ValueError('local_site_requires_root_prefix: build Eleventy with GITHUB_ACTIONS unset')

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, payload, content_type='application/json; charset=utf-8'):
            body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            if content_type.startswith('application/json'):
                self.send_header('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def same_origin(self):
            hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            host = self.headers.get('Host')
            origin = self.headers.get('Origin')
            if host not in hosts or (origin is not None and origin != f'http://{host}'):
                self.reply(403, {'error': 'same_origin_required'})
                return False
            return True

        def do_GET(self):
            if not self.same_origin():
                return
            path = urlsplit(self.path).path
            try:
                if path == '/api/ontology':
                    self.reply(200, ontology_reference())
                elif path == '/api/procedures':
                    self.reply(200, {'procedures': list_procedures(root)})
                elif path.startswith('/api/adjudication/'):
                    self.reply(200, open_adjudication(root, path.removeprefix('/api/adjudication/')))
                elif path.startswith('/api/analysis/'):
                    self.reply(200, analyze_procedure(root, path.removeprefix('/api/analysis/')))
                elif path.startswith('/api/procedures/'):
                    self.reply(200, build_source_packet(root, path.removeprefix('/api/procedures/')))
                else:
                    decoded = unquote(path)
                    if '\\' in decoded or ':' in decoded or '..' in decoded.split('/') or '\x00' in decoded:
                        self.reply(404, {'error': 'not_found'})
                        return
                    candidate = (site_root / decoded.lstrip('/')).resolve()
                    if candidate.is_dir():
                        candidate = (candidate / 'index.html').resolve()
                    if not candidate.is_relative_to(site_root) or not candidate.is_file():
                        self.reply(404, {'error': 'not_found'})
                        return
                    mime = {'.js': 'text/javascript', '.mjs': 'text/javascript'}.get(candidate.suffix)
                    mime = mime or mimetypes.guess_type(candidate.name)[0] or 'application/octet-stream'
                    if mime.startswith('text/'):
                        mime += '; charset=utf-8'
                    self.reply(200, candidate.read_bytes(), mime)
            except ValueError as error:
                self.reply(404 if str(error) == 'unknown_procedure' else 409, {'error': str(error)})
            except (OSError, KeyError, StopIteration):
                self.reply(500, {'error': 'repository_input_unavailable'})

        def do_POST(self):
            if not self.same_origin():
                return
            try:
                if self.headers.get_content_type() != 'application/json':
                    raise ValueError('application_json_required')
                if self.headers.get('Transfer-Encoding'):
                    raise ValueError('transfer_encoding_not_supported')
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_BODY:
                    raise ValueError('invalid_body_size')
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict) or not isinstance(body.get('procedure_id'), str):
                    raise ValueError('invalid_procedure_id')
                path = urlsplit(self.path).path
                if path == '/api/artifacts/status':
                    if set(body) != {'procedure_id', 'artifacts'}:
                        raise ValueError('expected_artifact_status_fields')
                    response = {'freshness': validate_artifacts(root, body['artifacts'])}
                elif path == '/api/compile':
                    if set(body) != {'procedure_id', 'inputs'}:
                        raise ValueError('expected_procedure_id_and_inputs_only')
                    response = compile_procedure(root, body['procedure_id'], body['inputs'])
                elif path == '/api/adjudication/compile':
                    if set(body) != {'procedure_id', 'session', 'branch_id'}:
                        raise ValueError('expected_reviewed_compile_fields')
                    response = compile_adjudication(root, body['procedure_id'], body['session'], body['branch_id'])
                elif path == '/api/adjudication/decision':
                    if set(body) != {'procedure_id', 'session', 'decision', 'branch_id'}:
                        raise ValueError('expected_reviewed_decision_fields')
                    response = apply_adjudication_decision(root, body['procedure_id'], body['session'], body['decision'], body['branch_id'])
                elif path == '/api/adjudication/branch':
                    if set(body) != {'procedure_id', 'session', 'branch_id', 'from_branch'}:
                        raise ValueError('expected_reviewed_branch_fields')
                    response = branch_adjudication(root, body['procedure_id'], body['session'], body['branch_id'], body['from_branch'])
                elif path == '/api/adjudication/execute':
                    if set(body) != {'procedure_id', 'session', 'branch_id', 'inputs'}:
                        raise ValueError('expected_reviewed_execute_fields')
                    response = execute_adjudication(root, body['procedure_id'], body['session'], body['branch_id'], body['inputs'])
                else:
                    self.reply(404, {'error': 'not_found'})
                    return
                self.reply(200, response)
            except (ValueError, UnicodeError) as error:
                self.reply(400, {'error': str(error)})
            except (OSError, KeyError, StopIteration):
                self.reply(500, {'error': 'repository_input_unavailable'})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8789)
    parser.add_argument('--site-dir', type=Path, help='Eleventy build directory (default: .cache/workbench/site)')
    args = parser.parse_args()
    server = make_server(Path(__file__).resolve().parents[1], args.port, args.site_dir)
    print(f'Procedure Workbench: http://127.0.0.1:{server.server_port}/adjudication/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
