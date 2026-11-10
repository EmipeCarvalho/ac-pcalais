"""Download sequencial de imagens públicas declaradas em um manifesto CSV.
Não executa conteúdo baixado. Não faz scraping de páginas nem usa credenciais.
"""
import argparse
import hashlib
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse, urljoin
import pandas as pd
import requests
from PIL import Image
import io

def public_url(url):
    parsed=urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Use URL pública HTTPS sem credenciais.')
    for address in socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(address[4][0]).is_global:
            raise ValueError('Destinos de rede privados não são aceitos.')

def download(url):
    for _ in range(5):
        public_url(url)
        with requests.get(url,timeout=30,stream=True,allow_redirects=False) as response:
            if response.is_redirect:
                url=urljoin(url,response.headers['Location']); continue
            response.raise_for_status()
            data=bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data)>20*1024*1024:
                    raise ValueError('Imagem acima de 20 MB.')
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            return bytes(data)
    raise ValueError('Muitos redirecionamentos.')

def collect(manifest):
    frame=pd.read_csv(manifest).fillna('')
    rows=[]
    for row in frame.to_dict('records'):
        path=Path(row['local_path']).resolve()
        # Restrito a data/ para evitar sobrescrita de código ou configuração.
        if not path.is_relative_to(Path('data').resolve()):
            raise ValueError('local_path precisa estar dentro de data/.')
        path.parent.mkdir(parents=True,exist_ok=True)
        try:
            data=download(row['source_url'])
            path.write_bytes(data)
            row.update(sha256=hashlib.sha256(data).hexdigest(),download_status='ok')
        except Exception as exc:
            row.update(sha256='',download_status=type(exc).__name__)
        rows.append(row)
    target=Path('data/collection.csv')
    pd.DataFrame(rows).to_csv(target,index=False)
    print(f'{sum(r["download_status"]=="ok" for r in rows)}/{len(rows)} imagens baixadas. Auditoria: {target}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');collect(p.parse_args().manifest)
