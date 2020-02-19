import argparse
import base64
import binascii
import math
import os
import re
import subprocess
import urllib.request

from Crypto import Random
from Crypto.Cipher import AES
from tqdm.cli import tqdm

KEY = b"1234567890123456"
IV = b"1234567890123456"

UA = 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0'

IDENT_REG = re.compile(r'pdffile/([a-zA-Z0-9=]+)')
OPENKEY_REG = re.compile(r'[a-zA-Z0-9=]{10,}')

PAGES_PER_BATCH = 10
CODE_EXISTS = 98


def _curl_download(url, output):
    if os.path.exists(output):
        print(f"File {output} exists. Skipping...")
        return CODE_EXISTS
    return subprocess.call(['curl', url, '-H', UA, '--compressed'])


def _wget_download(url, output):
    if os.path.exists(output):
        print(f"File {output} exists. Skipping...")
        return CODE_EXISTS
    return subprocess.call(['wget', url, '--header', UA, '-O', output])


def _decrypt_pdf(filename, output, password):
    return subprocess.call(
        ['pdftk', filename, 'input_pw', password, 'output', output])


def _merge_pdfs(files, output):
    return subprocess.call(['pdfunite', *files, output])


def _format_pdf(ident, batch=0):
    return f"https://pdfxz.pmph.com/pdffile/{ident}/{batch}_{ident}.pdf"


def _get_openkey(ident):
    script_url = f"https://pdfxz.pmph.com/pdffile/{ident}/{ident}.js"
    script = urllib.request.urlopen(script_url).read().decode('utf-8')
    return OPENKEY_REG.findall(script)[0]


def _get_ident_from_url(url):
    data = urllib.request.urlopen(url).read().decode('utf-8')
    return IDENT_REG.findall(data)[0]


def decrypt(word, keyStr=KEY, key=KEY, iv=IV):
    aes = AES.new(key, mode=AES.MODE_CBC, IV=iv)
    decrypted = aes.decrypt(binascii.a2b_base64(word))
    return decrypted


def download(ident, num_batches=None):
    open_key = _get_openkey(ident)
    print("PASSWORD:", decrypt(open_key).decode('utf-8'))

    if not os.path.exists(ident):
        os.mkdir(ident)

    # Download pdf files
    if num_batches is not None:
        for batch in tqdm(range(num_batches)):
            print(f"Downloading batch {batch} of {num_batches}...")
            _wget_download(_format_pdf(ident, batch),
                           output=f"{ident}/{batch}_{ident}.pdf")
    else:
        batch = 0
        while True:
            try:
                print(f"Downloading batch {batch * PAGES_PER_BATCH}...")
                retcode = _wget_download(_format_pdf(ident, batch),
                                         output=f"{ident}/{batch}_{ident}.pdf")
                if retcode != 0 and retcode != CODE_EXISTS:
                    raise Exception(f"Failed to download batch {batch}")
            except Exception as e:
                os.remove(f"{ident}/{batch}_{ident}.pdf")
                break
            batch += 1
        num_batches = batch + 1

    # Write to password.txt
    password = decrypt(open_key).decode('utf-8')
    print("PASSWORD:", password)
    with open(f"{ident}/password.txt", 'w') as f:
        f.write(password)

    # Decrypt
    files = []
    print("\nDecrypting files...")
    for i in tqdm(range(num_batches)):
        _decrypt_pdf(f"{ident}/{i}_{ident}.pdf", f"/tmp/pmph_temp_{i}.pdf",
                     password)
        files.append(f"/tmp/pmph_temp_{i}.pdf")

    # Merge
    print("\nMerging files...")
    _merge_pdfs(files, f"{ident}/{ident}.pdf")

    # Cleanup
    print("\nCleaning up...")
    for f in files:
        os.remove(f)

    for i in range(num_batches):
        os.remove(f"{ident}/{i}_{ident}.pdf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--ident',
                        help="PDF Identifier (window.pdfIdentify)",
                        default=None)
    parser.add_argument('--url', help="The url of the pdf page", default=None)
    parser.add_argument('-p',
                        '--pages',
                        type=int,
                        help="Total number of pages in the pdf file",
                        default=None)
    args = parser.parse_args()

    if args.url is not None:
        ident = _get_ident_from_url(args.url)
    elif args.ident is not None:
        ident = args.ident
    else:
        raise Exception(
            "You must provide identifier or url to download the pdf file")

    if args.pages:
        pages = math.ceil(args.pages / PAGES_PER_BATCH)
    else:
        pages = None

    download(ident, pages)
