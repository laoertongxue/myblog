"""Reproducible D9 download archives, standard library only."""
import hashlib
import json
from pathlib import Path
import zipfile

REPO=Path(__file__).resolve().parents[1]
SLUG='seasonal-naive-demand-forecast'
OUT=REPO/'static/downloads'


def pack(name, entries):
    entries=dict(entries)
    entries['MANIFEST.sha256']=''.join(f'{hashlib.sha256(data).hexdigest()}  {path}\n' for path,data in sorted(entries.items())).encode()
    path=OUT/name
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,11,2,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert all(archive.read(name)==data for name,data in entries.items())
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size,'entries':len(entries)}


def tree(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}


if __name__=='__main__':
    practice=tree(REPO/'examples/d9-seasonal-naive')
    practice.update({f'review/{p.name}':p.read_bytes() for p in (REPO/'docs').glob('d9-review-*')
                     if p.is_file() and p.name!='d9-review-round2-archives.json'})
    practice['review/README.txt']='这里保存独立审查的原始记录和脚本。审查脚本保留完整站点仓库的docs/相对路径，需在laoertongxue/myblog仓库根执行python docs/<脚本名>；图片/压缩包审查还需要仓库配图与static/downloads。不把这些归档脚本当作独立实践包入口。独立实验入口是根目录run.py与test_baseline.py。\n'.encode('utf-8')
    figures=tree(REPO/f'content/blog/{SLUG}/images')
    figures={f'png/{name}':data for name,data in figures.items()}
    figures.update({f'svg/{name}':data for name,data in tree(REPO/f'assets/diagram-sources/{SLUG}').items()})
    figures['svg/d9-00_cover.svg']=(REPO/f'assets/cover-sources/{SLUG}.svg').read_bytes()
    figures['README.txt']='D9-v1 教学模拟。PNG逐像素黑白灰；封面900×383，正文保持原比例。图3为验证实际结果，其余为依据规则与实测输出排版的解释图。SVG可编辑。\n'.encode('utf-8')
    article=tree(REPO/f'content/blog/{SLUG}')
    article['README.txt']='打开index.md阅读；images为相对图片目录。实践包和配图源文件包另行提供。全部情景模拟，无经营收益声明。\n'.encode('utf-8')
    print(json.dumps([pack('d9-seasonal-naive-practice.zip',practice),pack('d9-seasonal-naive-images.zip',figures),pack('d9-seasonal-naive-article.zip',article)],indent=2))
