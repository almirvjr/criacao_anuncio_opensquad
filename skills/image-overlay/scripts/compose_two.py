#!/usr/bin/env python3
"""
Compoe dois produtos de fundo creme (ex.: lixeira + caixa) lado a lado num canvas
creme reconstruido, cada um escalado/posicionado por alvo (centro-x, base-y),
fundindo por alpha suave (sem recorte de mascara). Objetos nao se sobrepoem;
as regioes de creme se sobrepoem inofensivamente.
"""
import argparse
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
import cutout

def bbox_of(img, thr=40):
    # BiRefNet (cutout.py) com fallback automatico pra heuristica antiga.
    return cutout.mask_bbox(img)

def feather(nw,nh,inset=70,blur=36):
    a=Image.new("L",(nw,nh),0); ImageDraw.Draw(a).rectangle([inset,inset,nw-inset,nh-inset],fill=255)
    return a.filter(ImageFilter.GaussianBlur(blur))

def place(canvas, src, scale, cx, base_y):
    l,t,r,b=bbox_of(src); ocx=(l+r)/2
    nw,nh=int(src.width*scale),int(src.height*scale)
    s=src.resize((nw,nh),Image.LANCZOS); s.putalpha(feather(nw,nh))
    px=int(cx-ocx*scale); py=int(base_y-b*scale)
    canvas.alpha_composite(s,(px,py))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bin",required=True); ap.add_argument("--box",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    binimg=Image.open(a.bin).convert("RGB"); box=Image.open(a.box).convert("RGB")
    W,H=binimg.size
    arr=np.asarray(binimg).astype(np.float32)
    edge=np.concatenate([arr[:, :40, :], arr[:, W-40:, :]],axis=1)
    prof=np.median(edge,axis=1); canv=np.repeat(prof[:,None,:],W,axis=1)
    canvas=Image.fromarray(np.clip(canv,0,255).astype(np.uint8),"RGB").convert("RGBA")
    # caixa proporcional em pe ao lado (direita), mesmo chao
    place(canvas, box, 0.66, 850, 716)
    # lixeira na frente (esquerda)
    place(canvas, binimg, 0.52, 410, 716)
    canvas.convert("RGB").save(a.out, quality=93)
    print("OK", a.out)

if __name__=="__main__": main()
