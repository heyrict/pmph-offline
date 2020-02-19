# Pmph Download
该脚本用于新型冠状病毒防疫期间下载人卫教材电子版 pdf 使用。

详见：https://www.pmph.com/main/about?articleId=21150

**下载所得 pdf 版权归人民卫生出版社所有。代码基于 MIT 协议开源。**

## Pre-requisition
- `pdftk`
- poppler, specifically `pdfunite` binary
- python, with packages installed with `pip install -r requirements.txt`

## Usage
```
usage: pmph-download.py [-h] [-i IDENT] [--url URL] [-p PAGES]

optional arguments:
  -h, --help            show this help message and exit
  -i IDENT, --ident IDENT
                        PDF Identifier (window.pdfIdentify)
  --url URL             The url of the pdf page
  -p PAGES, --pages PAGES
                        Total number of pages in the pdf file
```

Example: `python pmph-download.py --url https://www.pmph.com/main/pdfview/2054`
