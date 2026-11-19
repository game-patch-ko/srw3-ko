import srwtext
rom=open(srwtext.SRC,'rb').read()
LEN={0xF0:4,0xF1:3,0xF2:2,0xF3:1,0xF4:2,0xF5:2,0xF6:3,0xF7:5,0xF8:4,0xF9:4,0xFA:2,0xFB:1,0xFC:3,0xFD:3,0xFE:2}
def lparse(o, text=False, limit=4000):
    i=o; out=[]
    while i<o+limit:
        c=rom[i]
        if c==0xFF: return out,i+1,text
        if text and c in (0xF0,0xF1,0xF2): out.append(('k',i)); i+=2; continue
        if c>=0xF0 and not (text and c<0xF3):
            if c==0xF4: text=bool(rom[i+1]&0x40)
            out.append(('c%02X'%c,i)); i+=LEN[c]; continue
        out.append(('t' if not text else 'ch',i)); i+=1
    return out,i,text
for idx in (0,1,2,8):
    v=rom[0x5277+3*idx]|rom[0x5278+3*idx]<<8|rom[0x5279+3*idx]<<16
    T=srwtext.s2f(v)
    n=srwtext.table_len(rom,T,set())
    bank=T//0x8000
    ws=[rom[T+2*k]|rom[T+2*k+1]<<8 for k in range(n)]
    tg=[bank*0x8000+w-0x8000 for w in ws if w>=0x8000]
    nt=sum(1 for t in set(tg) if any(k=='ch' or k=='k' for k,_ in lparse(t)[0]))
    print('D277[%02X] table %06X n=%d unique=%d with-text=%d'%(idx,T,n,len(set(tg)),nt))
