#!/usr/bin/env python3
"""
Encolhe o produto de uma base de estudio (fundo creme liso) e o reposiciona
mais alto, sobre um fundo creme reconstruido, pra caber INTEIRO acima da faixa.
Deterministico (sem mascara de produto): escala a imagem toda e funde por alpha
suave num canvas creme feito do gradiente das bordas.

Uso: python fit_scale.py BASE OUT --scale 0.72 --base-y 660
"""
import argparse, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
import cutout

def product_bottom(img):
    # BiRefNet (cutout.py) com fallback automatico pra heuristica antiga.
    return cutout.product_bottom(img)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("out")
    ap.add_argument("--scale",type=float,default=0.72)
    ap.add_argument("--base-y",type=int,default=660)
    a=ap.parse_args()
    im=Image.open(a.base).convert("RGB"); W,H=im.size

    # canvas creme a partir do gradiente das colunas de borda (sem produto)
    arr=np.asarray(im).astype(np.float32)
    edge=np.concatenate([arr[:, :40, :], arr[:, W-40:, :]], axis=1)
    prof=np.median(edge, axis=1)                 # (H,3)
    canvas=np.repeat(prof[:,None,:], W, axis=1)
    canvas=Image.fromarray(np.clip(canvas,0,255).astype(np.uint8),"RGB")

    pb=product_bottom(im)
    nw=int(W*a.scale); nh=int(H*a.scale)
    scaled=im.resize((nw,nh), Image.LANCZOS)
    paste_x=(W-nw)//2
    paste_y=a.base_y-int(pb*a.scale)

    # alpha suave (retangulo inset + blur) pra fundir o creme do scaled no canvas
    alpha=Image.new("L",(nw,nh),0); d=ImageDraw.Draw(alpha)
    inset=70
    d.rectangle([inset,inset,nw-inset,nh-inset], fill=255)
    alpha=alpha.filter(ImageFilter.GaussianBlur(38))
    scaled.putalpha(alpha)
    canvas=canvas.convert("RGBA"); canvas.alpha_composite(scaled,(paste_x,paste_y))
    canvas.convert("RGB").save(a.out, quality=93)
    print("OK", a.out, "scale",a.scale,"base_y",a.base_y)

if __name__=="__main__": main()
