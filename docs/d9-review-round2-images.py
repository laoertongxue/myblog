"""Independent PNG dimension and pixel equality check; Python stdlib only."""
from pathlib import Path
import struct
import zlib
import json
import hashlib

root=Path(__file__).resolve().parents[1]
results=[]
for path in sorted((root/'content/blog/seasonal-naive-demand-forecast/images').glob('*.png')):
    raw=path.read_bytes()
    assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    offset=8; chunks=[]
    while offset<len(raw):
        length=struct.unpack('>I',raw[offset:offset+4])[0]
        kind=raw[offset+4:offset+8]
        data=raw[offset+8:offset+8+length]
        assert zlib.crc32(kind+data)&0xffffffff==struct.unpack('>I',raw[offset+8+length:offset+12+length])[0]
        if kind==b'IHDR': w,h,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',data)
        if kind==b'IDAT': chunks.append(data)
        offset+=12+length
    assert depth==8 and color in (2,6) and interlace==0
    channels=3 if color==2 else 4
    decoded=zlib.decompress(b''.join(chunks));stride=w*channels
    previous=bytearray(stride);offset=0;mismatch=0
    def paeth(a,b,c):
        p=a+b-c;pa=abs(p-a);pb=abs(p-b);pc=abs(p-c)
        return a if pa<=pb and pa<=pc else b if pb<=pc else c
    for y in range(h):
        mode=decoded[offset];offset+=1
        row=bytearray(decoded[offset:offset+stride]);offset+=stride
        for i in range(stride):
            left=row[i-channels] if i>=channels else 0
            up=previous[i]
            corner=previous[i-channels] if i>=channels else 0
            if mode==1:row[i]=(row[i]+left)&255
            elif mode==2:row[i]=(row[i]+up)&255
            elif mode==3:row[i]=(row[i]+(left+up)//2)&255
            elif mode==4:row[i]=(row[i]+paeth(left,up,corner))&255
            else:assert mode==0
        mismatch+=sum(row[i]!=row[i+1] or row[i+1]!=row[i+2] for i in range(0,stride,channels))
        previous=row
    assert mismatch==0,path
    if 'cover' in path.name:assert (w,h)==(900,383)
    results.append({'name':path.name,'width':w,'height':h,'pixels':w*h,'rgb_unequal':mismatch,'sha256':hashlib.sha256(raw).hexdigest()})
assert len(results)==5
(root/'docs/d9-review-round2-images.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
