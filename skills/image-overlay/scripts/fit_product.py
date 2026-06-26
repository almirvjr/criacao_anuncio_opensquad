#!/usr/bin/env python3
"""
Encolhe e reposiciona o produto numa base de estudio (fundo creme liso),
pra ele caber INTEIRO acima da faixa do overlay. Reconstroi o fundo a partir
de colunas sem produto e recompoe o produto (com sombra) por mascara de diferenca.

Uso: python fit_product.py BASE OUT [--scale 0.72] [--base-y 695]
"""
import argparse
from PIL import Image, ImageFilter
import numpy as np

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("out")
    ap.add_argument("--scale",type=float,default=0.72)
    ap.add_argument("--base-y",type=int,default=695)
    a=ap.parse_args()
    im=Image.open(a.base).convert("RGB"); W,H=im.size
    arr=np.asarray(im).astype(np.float32)

    # perfil de fundo por linha = mediana das colunas de borda (sem produto)
    edge=np.concatenate([arr[:, :40, :], arr[:, W-40:, :]], axis=1)
    prof=np.median(edge, axis=1)               # (H,3)
    bg=np.repeat(prof[:,None,:], W, axis=1)     # (H,W,3) gradiente vertical

    # mascara do produto = diferenca da estimativa de fundo
    diff=np.sqrt(((arr-bg)**2).sum(axis=2))
    m=(diff>16).astype(np.uint8)*255
    mask=Image.fromarray(m,"L").filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2))

    bg_img=Image.fromarray(np.clip(bg,0,255).astype(np.uint8),"RGB")
    prod=im.copy(); prod.putalpha(mask)

    # bbox do produto
    bbox=mask.point(lambda p:255 if p>30 else 0).getbbox()
    prod_c=prod.crop(bbox)
    nw=int(prod_c.width*a.scale); nh=int(prod_c.height*a.scale)
    prod_s=prod_c.resize((nw,nh), Image.LANCZOS)

    canvas=bg_img.copy()
    x=(W-nw)//2
    y=a.base_y-nh
    canvas.paste(prod_s,(x,y),prod_s)
    canvas.save(a.out, quality=93)
    print("OK", a.out, canvas.size, "produto base_y=",a.base_y,"scale=",a.scale)

if __name__=="__main__": main()
