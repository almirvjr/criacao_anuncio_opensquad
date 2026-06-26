#!/usr/bin/env python3
"""
Renderizador deterministico do arquetipo FAIXA CLARA (overlay StorySelling) via Pillow.
Substitui o render por browser (chrome-devtools instavel no Windows: dpr/janela variam).
Saida exata 1200x1200. Reaproveitavel pro lote das 9 fotos.

Uso:
  python render_faixa.py --config caminho.json
Config JSON: { base, output, eyebrow, headline_ink, headline_accent, sub,
               selos:[...], slogan, logo, logo_align: "left"|"center" }
"""
import argparse, json, os, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
import numpy as np
import cutout
import framing_gate

FONT = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "Montserrat.ttf")

PAPER=(246,241,233); BROWN=(84,29,3); TERRA=(235,178,138)
GREEN=(34,141,64); INK=(15,15,15); INK_SOFT=(110,91,78)
W=H=1200; PAD=64

def font(size, weight):
    f=ImageFont.truetype(FONT, size); f.set_variation_by_axes([weight]); return f

def tlen(draw,s,f): return draw.textlength(s,font=f)

def tracked(draw, xy, text, f, fill, tracking):
    x,y=xy
    for ch in text:
        draw.text((x,y), ch, font=f, fill=fill)
        x += tlen(draw,ch,f) + tracking
    return x

def check_chip(img, draw, cx, cy, r=16):
    draw.ellipse([cx-r,cy-r,cx+r,cy+r], fill=GREEN)
    # checkmark em branco
    draw.line([(cx-7,cy+1),(cx-2,cy+6),(cx+8,cy-6)], fill=(255,255,255), width=4, joint="curve")

def product_bbox(img):
    return cutout.mask_bbox(img)

def _arrowhead(draw,tip,frm,color,head=13):
    ang=math.atan2(tip[1]-frm[1], tip[0]-frm[0])
    a1=(tip[0]-head*math.cos(ang-0.5), tip[1]-head*math.sin(ang-0.5))
    a2=(tip[0]-head*math.cos(ang+0.5), tip[1]-head*math.sin(ang+0.5))
    draw.polygon([tip,a1,a2], fill=color)

def _dashed_line(draw, p0, p1, color, width=1, dash=9, gap=6):
    # linha tracejada generica (serve p/ horizontal, vertical e diagonal)
    x0,y0=p0; x1,y1=p1; dx=x1-x0; dy=y1-y0
    dist=math.hypot(dx,dy)
    if dist==0: return
    ux,uy=dx/dist, dy/dist; n=0.0
    while n<dist:
        n2=min(n+dash, dist)
        draw.line([(x0+ux*n, y0+uy*n),(x0+ux*n2, y0+uy*n2)], fill=color, width=width)
        n+=dash+gap

def _vlabel(img, x_right, ycenter, text, f, fill):
    tw=ImageDraw.Draw(img).textlength(text,font=f)
    ti=Image.new("RGBA",(int(tw)+10,f.size+12),(0,0,0,0)); ImageDraw.Draw(ti).text((0,0),text,font=f,fill=fill)
    ti=ti.rotate(90,expand=True)
    img.paste(ti,(int(x_right-ti.width),int(ycenter-ti.height//2)),ti)

def _mask_of(img):
    return cutout.alpha_mask(img)

def draw_tecnica(img, draw, cfg):
    style=cfg.get("dim_style","modelo")
    mask=_mask_of(img); l,t,r,b=mask.getbbox()
    ma=np.asarray(mask)>0; ymid=(t+b)//2
    # colunas do produto na linha media, direto da mascara (BiRefNet ja exclui sombra/fundo)
    cols=np.where(ma[ymid])[0]
    cl,cr=(int(cols.min()),int(cols.max())) if len(cols) else (l,r)
    col=BROWN; f=font(31,800); A=cfg["dim_altura"]; Wd=cfg["dim_largura"]

    if style=="cotas":
        xd=l-66
        draw.line([(l-6,t),(xd-4,t)],fill=col,width=1); draw.line([(l-6,b),(xd-4,b)],fill=col,width=1)
        draw.line([(xd,t),(xd,b)],fill=col,width=2)
        _arrowhead(draw,(xd,t),(xd,t+26),col,12); _arrowhead(draw,(xd,b),(xd,b-26),col,12)
        _vlabel(img,xd-10,ymid,A,f,col)
        yd=b+66
        draw.line([(cl,b+6),(cl,yd-4)],fill=col,width=1); draw.line([(cr,b+6),(cr,yd-4)],fill=col,width=1)
        draw.line([(cl,yd),(cr,yd)],fill=col,width=2)
        _arrowhead(draw,(cl,yd),(cl+26,yd),col,12); _arrowhead(draw,(cr,yd),(cr-26,yd),col,12)
        w=draw.textlength(Wd,font=f); draw.text(((cl+cr)//2-w/2,yd+9),Wd,font=f,fill=col)

    elif style=="finas":
        # ESTILO DO MODELO DO ALMIR: cota de engenharia com LINHAS DE CHAMADA (extensao),
        # seta DUPLA nas duas pontas, largura DIAGONAL na base. Ref. BASE sem sombra; folga uniforme.
        col2=(74,55,42); ch=font(24,700); tilt=0.17; g=34
        dashed=cfg.get("dim_dashed", False)          # linhas tracejadas (estilo planta tecnica)
        labelbox=cfg.get("dim_label_box", True)       # caixinha creme atras do numero
        ext=cfg.get("dim_extension", True)            # linhas de chamada (produto -> linha de cota)
        def L(p0,p1,w):                               # linha continua OU tracejada conforme flag
            if dashed: _dashed_line(draw,p0,p1,col2,width=w)
            else: draw.line([p0,p1],fill=col2,width=w)
        bb=ma[max(0,b-150):b-3]; bc=np.where(bb.any(axis=0))[0]   # base real (mascara, sem sombra)
        bl=int(bc.min()) if len(bc) else cl
        br=cr+(cl-bl)                          # base direita simetrica (ignora pedal)
        # ---- ALTURA (vertical, seta dupla, linhas de chamada no topo e na base) ----
        hx=bl-g
        if ext:
            L((cl,t),(hx-3,t),1)     # chamada superior (topo do produto)
            L((bl,b),(hx-3,b),1)     # chamada inferior (base)
        L((hx,t),(hx,b),2)       # linha de cota
        _arrowhead(draw,(hx,t),(hx,t+24),col2,10); _arrowhead(draw,(hx,b),(hx,b-24),col2,10)
        cwA=draw.textlength(A,font=ch); myA=(t+b)//2
        if labelbox:
            draw.rounded_rectangle([hx-cwA-34,myA-22,hx-12,myA+22],radius=11,fill=(251,246,239))
        draw.text((hx-cwA-23,myA-15),A,font=ch,fill=col2)
        # ---- LARGURA (diagonal na base, seta dupla, linhas de chamada nas quinas) ----
        wyl=b+g; wyr=b+g+int(tilt*(br-bl))
        if ext:
            L((bl,b),(bl,wyl+3),1)   # chamada esquerda
            L((br,b),(br,wyr+3),1)   # chamada direita
        L((bl,wyl),(br,wyr),2)   # linha de cota
        _arrowhead(draw,(bl,wyl),(bl+24,wyl+int(tilt*24)),col2,10)
        _arrowhead(draw,(br,wyr),(br-24,wyr-int(tilt*24)),col2,10)
        mx=(bl+br)//2; my=(wyl+wyr)//2; cwW=draw.textlength(Wd,font=ch)
        if labelbox:
            draw.rounded_rectangle([mx-cwW/2-16,my+12,mx+cwW/2+16,my+56],radius=11,fill=(251,246,239))
        draw.text((mx-cwW/2,my+19),Wd,font=ch,fill=col2)

    else:  # modelo
        xv=l-46
        draw.line([(xv,t),(xv,b)],fill=col,width=2)
        draw.line([(xv-9,t),(xv+9,t)],fill=col,width=2); draw.line([(xv-9,b),(xv+9,b)],fill=col,width=2)
        _arrowhead(draw,(xv,t),(xv,t+24),col,10); _arrowhead(draw,(xv,b),(xv,b-24),col,10)
        _vlabel(img,xv-12,ymid,A,f,col)
        yh=b+34
        draw.line([(cl,yh),(cr,yh)],fill=col,width=2)
        draw.line([(cl,yh-9),(cl,yh+9)],fill=col,width=2); draw.line([(cr,yh-9),(cr,yh+9)],fill=col,width=2)
        _arrowhead(draw,(cl,yh),(cl+24,yh),col,10); _arrowhead(draw,(cr,yh),(cr-24,yh),col,10)
        w=draw.textlength(Wd,font=f); draw.text(((cl+cr)//2-w/2,yh+9),Wd,font=f,fill=col)

    # selo de litragem = etiqueta/tag MAIOR, colada no topo-direito do produto
    if cfg.get("liters"):
        tf=font(31,800); txt=cfg["liters"]; tw=int(draw.textlength(txt,font=tf))
        tagw=tw+56; x=min(r+58, W-PAD-tagw); y=max(40, t-34)
        pill(draw,x,y,txt,tf,BROWN,padx=28,pady=14)

def pill(draw, x, y, text, f, bg, fg=(255,255,255), padx=22, pady=12):
    w=draw.textlength(text,font=f); h=f.size
    draw.rounded_rectangle([x,y,x+w+2*padx,y+h+2*pady], radius=(h+2*pady)//2, fill=bg)
    draw.text((x+padx,y+pady-2), text, font=f, fill=fg)
    return y+h+2*pady

def _wrap_segments(draw, segments, f, maxw):
    # segments: [(texto, cor)] -> quebra em linhas preservando a cor por palavra
    words=[]
    for text,color in segments:
        for p in text.split(): words.append((p,color))
    sp=draw.textlength(" ",font=f)
    lines=[]; cur=[]; curw=0
    for word,color in words:
        ww=draw.textlength(word,font=f)
        add = ww if not cur else curw+sp+ww
        if cur and add>maxw: lines.append(cur); cur=[(word,color)]; curw=ww
        else: cur.append((word,color)); curw=add
    if cur: lines.append(cur)
    return lines

def _draw_segment_lines(draw, x, y, lines, f, line_h, shadow=True):
    sp=draw.textlength(" ",font=f)
    for line in lines:
        cx=x
        for i,(word,color) in enumerate(line):
            if i>0: cx+=sp
            if shadow: draw.text((cx+2,y+3),word,font=f,fill=(0,0,0))
            draw.text((cx,y),word,font=f,fill=color); cx+=draw.textlength(word,font=f)
        y+=line_h
    return y

def render_scrim(cfg):
    # ARQUETIPO SCRIM: foto full-bleed + degrade escuro embaixo + texto branco.
    base=Image.open(cfg["base"]).convert("RGB")
    if base.size!=(W,H): base=base.resize((W,H), Image.LANCZOS)
    img=base.convert("RGBA")
    sh=cfg.get("scrim_h",760); amax=cfg.get("scrim_alpha",205)
    ramp=np.linspace(0,amax,sh).astype(np.uint8)          # 0 no topo do scrim -> amax embaixo
    grad=np.zeros((sh,W,4),np.uint8); grad[...,3]=ramp[:,None]
    img.alpha_composite(Image.fromarray(grad,"RGBA"),(0,H-sh))
    img=img.convert("RGB"); draw=ImageDraw.Draw(img)

    WHITE=(255,255,255); SOFT=(228,222,214)
    accent=tuple(cfg.get("accent_color",[120,212,140]))   # verde claro: le bem no escuro
    x0=PAD
    # assinatura no rodape (texto, sem logo escuro que sumiria no fundo)
    bf=font(23,800); slf=font(15,500)
    brand=cfg.get("brand","TERRA CASA DECOR"); slogan=cfg.get("slogan","")
    block_bottom=H-48
    sl_y=block_bottom-20; brand_y=sl_y-30
    # bloco principal (eyebrow + headline + sub), ancorado ACIMA da assinatura
    hsz=cfg.get("headline_size",52); hf=font(hsz,800); line_h=hsz+10
    sf=font(24,500); maxw=W-2*PAD
    eb=cfg.get("eyebrow",""); sub=cfg.get("sub","")
    badge=cfg.get("badge",""); cta=cfg.get("cta","")
    hlines=_wrap_segments(draw,[(cfg.get("headline_ink",""),WHITE),(cfg.get("headline_accent",""),accent)],hf,maxw)
    ctaf=font(22,800); bdf=font(20,600)
    eb_h = 34 if eb else 0
    h_block = len(hlines)*line_h
    sub_h = 32 if sub else 0
    badge_h = 42 if badge else 0
    cta_h = (ctaf.size+2*14+18) if cta else 0
    total = eb_h + h_block + 16 + sub_h + badge_h + cta_h
    start_y = brand_y - 30 - total
    y=start_y
    if eb: tracked(draw,(x0+2,y), eb.upper(), font(20,700), accent, 3); y+=eb_h
    y=_draw_segment_lines(draw,x0,y,hlines,hf,line_h); y+=16
    if sub:
        draw.text((x0+2,y+2), sub, font=sf, fill=(0,0,0))
        draw.text((x0,y), sub, font=sf, fill=SOFT); y+=sub_h
    if badge:
        check_chip(img,draw,x0+13,y+13,13)
        draw.text((x0+35,y+1), badge, font=bdf, fill=(0,0,0)); draw.text((x0+34,y), badge, font=bdf, fill=WHITE); y+=badge_h
    if cta:
        pill(draw, x0, y, cta, ctaf, GREEN)
    # assinatura: SEM marca nas imagens do anuncio por padrao (Almir 19/06 — nao prender a foto a um rebrand).
    # So desenha logo/slogan se cfg["show_brand"] == true (legado/excecao).
    if cfg.get("show_brand") and cfg.get("brand_logo"):
        logo=Image.open(cfg["brand_logo"]).convert("RGBA")
        lh=cfg.get("brand_logo_h",70); lw=int(logo.width*lh/logo.height)
        logo=logo.resize((lw,lh), Image.LANCZOS)
        slogan=cfg.get("slogan",""); slf2=font(14,500)
        sl_h = 22 if slogan else 0
        ly=block_bottom-lh-sl_h+6
        if slogan:                                   # logo CENTRALIZADO no eixo do slogan (alinhado ao centro)
            sw=draw.textlength(slogan,font=slf2); slx=W-PAD-sw
            lx=int(slx+sw/2-lw/2)                     # centro do logo = centro do slogan
        else:
            lx=W-PAD-lw
        img.paste(logo,(lx,ly),logo)
        if slogan:
            sly=ly+lh+4
            draw.text((slx+1,sly+1),slogan,font=slf2,fill=(0,0,0)); draw.text((slx,sly),slogan,font=slf2,fill=SOFT)
    elif cfg.get("show_brand"):
        draw.text((x0+2,brand_y+2), brand, font=bf, fill=(0,0,0)); draw.text((x0,brand_y), brand, font=bf, fill=WHITE)
        draw.text((x0+1,sl_y+1), slogan, font=slf, fill=(0,0,0)); draw.text((x0,sl_y), slogan, font=slf, fill=SOFT)

    os.makedirs(os.path.dirname(os.path.abspath(cfg["output"])),exist_ok=True)
    img.save(cfg["output"], quality=93)
    print("OK", cfg["output"], img.size)

def render_plate(cfg):
    # ARQUETIPO PLATE: texto em ESPACO NEGATIVO limpo da cena (sem faixa, sem scrim).
    # Tinta escura com halo branco p/ legibilidade; nao cobre o produto (o produto fica
    # do outro lado do frame). Bake-in p/ lifestyle composto com area vazia reservada.
    base=Image.open(cfg["base"]).convert("RGB")
    if base.size!=(W,H): base=base.resize((W,H), Image.LANCZOS)
    img=base.copy(); draw=ImageDraw.Draw(img)
    x0=cfg.get("text_x",PAD); y=cfg.get("text_y",130); maxw=cfg.get("text_maxw",520)
    ink=tuple(cfg.get("ink_color",INK)); accent=tuple(cfg.get("accent_color",BROWN))
    halo=cfg.get("halo",True)
    def _halo(cx,cy,word,f):
        if halo:
            for dx,dy in [(-2,0),(2,0),(0,-2),(0,2),(2,2),(-2,-2)]:
                draw.text((cx+dx,cy+dy),word,font=f,fill=(255,255,255))
    eb=cfg.get("eyebrow","")
    if eb:
        # eyebrow com halo manual char-a-char (tracked)
        ef=font(19,700); cx=x0
        for ch in eb.upper():
            _halo(cx,y,ch,ef); draw.text((cx,y),ch,font=ef,fill=accent); cx+=tlen(draw,ch,ef)+3
        y+=34
    hf=font(cfg.get("headline_size",46),800); line_h=hf.size+8
    hlines=_wrap_segments(draw,[(cfg.get("headline_ink",""),ink),(cfg.get("headline_accent",""),accent)],hf,maxw)
    sp=draw.textlength(" ",font=hf)
    for line in hlines:
        cx=x0
        for i,(word,color) in enumerate(line):
            if i>0: cx+=sp
            _halo(cx,y,word,hf); draw.text((cx,y),word,font=hf,fill=color); cx+=draw.textlength(word,font=hf)
        y+=line_h
    y+=8
    sub=cfg.get("sub","")
    if sub:
        sf=font(cfg.get("sub_size",22),600)                 # mais peso p/ legibilidade
        sub_col=tuple(cfg.get("sub_color",(58,44,36)))      # escuro (era INK_SOFT claro demais)
        for line in _wrap_segments(draw,[(sub,sub_col)],sf,maxw):
            cx=x0
            for i,(word,color) in enumerate(line):
                if i>0: cx+=draw.textlength(" ",font=sf)
                _halo(cx,y,word,sf); draw.text((cx,y),word,font=sf,fill=color); cx+=draw.textlength(word,font=sf)
            y+=sf.size+6
    os.makedirs(os.path.dirname(os.path.abspath(cfg["output"])),exist_ok=True)
    img.save(cfg["output"], quality=93)
    print("OK(plate)", cfg["output"], img.size)


def render(cfg):
    if cfg.get("layout")=="scrim":
        return render_scrim(cfg)
    if cfg.get("layout")=="plate":
        return render_plate(cfg)
    base=Image.open(cfg["base"]).convert("RGB")
    if base.size!=(W,H): base=base.resize((W,H), Image.LANCZOS)
    BAND_H=cfg.get("band_h",486)
    band_top=H-BAND_H
    band_fade_h=40
    # ENQUADRAMENTO (gate inpulavel, 2026-06-24): a faixa-clara + seu fade NAO podem
    # cortar o produto. autofit previne; o gate (antes do save) barra -> _rejeitado/+exit3.
    if cfg.get("autofit", True):
        base, _fit = framing_gate.autofit(base, band_h=BAND_H, fade_h=band_fade_h)
        if _fit.get("changed"): print("[autofit]", _fit["motivo"])
    img=base.copy(); draw=ImageDraw.Draw(img)

    # modo técnico: setas de medida + selo de litros (sobre o produto, acima da faixa)
    if cfg.get("dim_altura"):
        draw_tecnica(img, draw, cfg)

    # fade suave acima da faixa (40px)
    fade_h=40
    fade=Image.new("RGBA",(W,fade_h),(0,0,0,0)); fd=fade.load()
    for yy in range(fade_h):
        a=int(255*(yy/fade_h))
        for xx in range(W): fd[xx,yy]=(PAPER[0],PAPER[1],PAPER[2],a)
    img.paste(Image.alpha_composite(img.crop((0,band_top-fade_h,W,band_top)).convert("RGBA"),fade).convert("RGB"),(0,band_top-fade_h))
    # faixa
    draw.rectangle([0,band_top,W,H], fill=PAPER)
    # filete terracota
    draw.rectangle([0,band_top,W,band_top+7], fill=TERRA)

    x0=PAD; y=band_top+46
    # eyebrow
    tracked(draw,(x0,y), cfg["eyebrow"].upper(), font(20,700), BROWN, 3); y+=20+13
    # headline (duas cores)
    hf=font(54,800)
    draw.text((x0,y), cfg["headline_ink"], font=hf, fill=INK)
    xacc=x0+tlen(draw,cfg["headline_ink"],hf)
    draw.text((xacc,y), cfg["headline_accent"], font=hf, fill=BROWN); y+=56+12
    # sub
    draw.text((x0,y), cfg["sub"], font=font(22,500), fill=INK_SOFT); y+=26+24

    # selos (2 colunas, row-major) — opcional
    selos=cfg.get("selos",[])
    if selos:
        sf=font(21,600); content_w=W-2*PAD; gap=40; colw=(content_w-gap)//2
        cols=[x0, x0+colw+gap]; pitch=46
        for i,s in enumerate(selos):
            col=i%2; row=i//2
            cx=cols[col]; cy=y+row*pitch+12
            check_chip(img,draw,cx+16,cy,16)
            draw.text((cx+16+16+11,cy-13), s, font=sf, fill=INK)
        y += ((len(selos)+1)//2)*pitch + 6
    # badge (pill) — opcional
    if cfg.get("badge"):
        pill(draw, x0, y, cfg["badge"], font(22,700), GREEN)

    # assinatura: SEM marca por padrao (Almir 19/06). So desenha logo/slogan se cfg["show_brand"]==true.
    if cfg.get("show_brand") and cfg.get("logo"):
        logo=Image.open(cfg["logo"]).convert("RGBA")
        lh=76; lw=int(logo.width*lh/logo.height); logo=logo.resize((lw,lh), Image.LANCZOS)
        slf=font(14,500); slogan=cfg.get("slogan","")
        sl_w=tlen(draw,slogan,slf)
        block_bottom=H-44
        sl_y=block_bottom-18
        logo_y=sl_y-9-lh
        align=cfg.get("logo_align","left")
        if align=="center":
            lx=(W-lw)//2; slx=(W-sl_w)//2
        elif align=="right":
            slx=int(W-PAD-sl_w); lx=int(slx+sl_w/2-lw/2)   # logo centralizado no eixo do slogan
        else:
            lx=x0; slx=x0+2
        img.paste(logo,(lx,logo_y),logo)
        draw.text((slx,sl_y), slogan, font=slf, fill=INK_SOFT)

    # GATE de enquadramento (inpulavel salvo cfg["no_qa"]): produto invadindo o fade -> _rejeitado/+exit3
    chk=framing_gate.check_clip(base, band_h=BAND_H, fade_h=band_fade_h)
    if not chk["ok"] and not cfg.get("no_qa"):
        rej=os.path.join(os.path.dirname(os.path.abspath(cfg["output"])),"_rejeitado")
        os.makedirs(rej,exist_ok=True)
        rp=os.path.join(rej,os.path.basename(cfg["output"]))
        img.save(rp,quality=93)
        print("[framing_gate] REPROVA |", chk["motivo"], "->", rp)
        sys.exit(3)
    print("[framing_gate] OK |", chk["motivo"])

    os.makedirs(os.path.dirname(os.path.abspath(cfg["output"])),exist_ok=True)
    img.save(cfg["output"], quality=93)
    print("OK", cfg["output"], img.size)

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--config",required=True)
    a=ap.parse_args()
    with open(a.config,encoding="utf-8") as f: render(json.load(f))
