"""Lossless 8-bit PNG tiling, using only standard library. No colorspace conversion."""
import struct,zlib
from pathlib import Path
def decode(path):
 b=Path(path).read_bytes()
 if b[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Not PNG')
 cursor=8;packed=[]
 while cursor<len(b):
  size=struct.unpack('>I',b[cursor:cursor+4])[0];kind=b[cursor+4:cursor+8];data=b[cursor+8:cursor+8+size];cursor+=size+12
  if kind==b'IHDR':w,h,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',data)
  if kind==b'IDAT':packed.append(data)
  if kind==b'IEND':break
 if depth!=8 or color not in [2,6] or interlace:raise ValueError('Expected noninterlaced8-bit RGB/RGBA PNG')
 channels=3 if color==2 else 4;stride=w*channels;raw=zlib.decompress(b''.join(packed));rows=[];previous=bytearray(stride)
 for y in range(h):
  offset=y*(stride+1);kind=raw[offset];row=bytearray(raw[offset+1:offset+1+stride])
  for x in range(stride):
   a=row[x-channels] if x>=channels else 0;b=previous[x];c=previous[x-channels] if x>=channels else 0
   if kind==1:value=a
   elif kind==2:value=b
   elif kind==3:value=(a+b)//2
   elif kind==4:
    p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c);value=a if pa<=pb and pa<=pc else b if pb<=pc else c
   elif kind==0:value=0
   else:raise ValueError('Unsupported PNG filter')
   row[x]=(row[x]+value)&255
  rows.append(bytes(row));previous=row
 return w,h,channels,rows
def encode(path,w,h,c,rows):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2 if c==3 else 6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r for r in rows),6))+chunk(b'IEND',b'');Path(path).write_bytes(data)
def assemble(paths,target):
 faces=[decode(p) for p in paths];w,h,c,_=faces[0]
 if len(faces)!=6 or w!=h or any(f[:3]!=(w,h,c) for f in faces):raise ValueError('Six equal square faces required')
 rows=[b''.join(faces[row*3+col][3][y] for col in range(3)) for row in range(2) for y in range(h)];encode(target,w*3,h*2,c,rows)
 aw,ah,ac,decoded=decode(target)
 for i,face in enumerate(faces):
  for y in range(h):
   if decoded[(i//3)*h+y][(i%3)*w*c:(i%3+1)*w*c]!=face[3][y]:raise ValueError('Atlas tile pixel mismatch')
 return {'pass':True,'decodedPixelExact':True,'tileSize':w,'layout':[['front','right','back'],['left','up','down']]}
