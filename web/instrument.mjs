import {shadowAt} from './model.mjs';

const TAU=Math.PI*2;
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
function random(seed) {let v=seed;return ()=>{v=(Math.imul(v,1664525)+1013904223)>>>0;return v/4294967296;};}
const rand=random(5913);
const grid=Array.from({length:128*128},()=>rand());
function noise(x,y){const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy;const u=fx*fx*(3-2*fx),v=fy*fy*(3-2*fy);const g=(a,b)=>grid[((b+1024)%128)*128+((a+1024)%128)];return (g(ix,iy)*(1-u)+g(ix+1,iy)*u)*(1-v)+(g(ix,iy+1)*(1-u)+g(ix+1,iy+1)*u)*v;}

export class Instrument {
  constructor(canvas){
    this.canvas=canvas;this.ctx=canvas.getContext('2d');
    this.size=420;this.surface=document.createElement('canvas');this.surface.width=this.surface.height=this.size;
    this.surfaceCtx=this.surface.getContext('2d');this.image=this.surfaceCtx.createImageData(this.size,this.size);
    this.terrain=new Float32Array(this.size*this.size);this.disc=[];
    const craters=Array.from({length:85},()=>({x:rand()*1.8-.9,y:rand()*1.8-.9,r:.008+rand()**3*.13}));
    const seas=[[-.34,-.3,.29],[-.04,-.45,.22],[.2,-.28,.25],[.42,-.03,.19],[-.48,.13,.26],[-.12,.07,.17],[.13,.31,.13]];
    for(let j=0;j<this.size;j++)for(let i=0;i<this.size;i++){
      const x=(i+.5)/this.size*2-1,y=(j+.5)/this.size*2-1,r2=x*x+y*y,idx=j*this.size+i;
      if(r2>1)continue;
      let n=0,weight=0;for(let octave=0;octave<6;octave++){const f=5*2**octave,w=.52**octave;n+=noise((x+2)*f,(y+2)*f)*w;weight+=w;}
      let value=155+80*n/weight;
      for(const [sx,sy,sr] of seas){const distance=Math.hypot(x-sx,y-sy);value-=55*Math.exp(-distance*distance/(sr*sr))*(.55+noise(x*17+50,y*17+50));}
      for(const crater of craters){const dx=x-crater.x,dy=y-crater.y,d=Math.hypot(dx,dy)/crater.r;if(d<1.4)value+=(-22*Math.exp(-d*d*3)+30*Math.exp(-(((d-.9)/.16)**2)))*(.8+(dx-dy)/crater.r*.25);}
      value*=.54+.46*Math.sqrt(1-r2);this.terrain[idx]=value;
      this.disc.push({idx,x,y});this.image.data[idx*4+3]=Math.round(clamp((1-Math.sqrt(r2))*this.size)*255);
    }
  }
  draw(event,progress){
    const c=this.ctx,C=450;c.clearRect(0,0,900,900);
    const circle=(r,stroke,width=1,start=0,end=TAU)=>{c.beginPath();c.arc(C,C,r,start,end);c.strokeStyle=stroke;c.lineWidth=width;c.stroke();};
    const text=(str,x,y,size=11,color='#747984',align='center')=>{c.font=`${size}px "SFMono-Regular",Consolas,monospace`;c.fillStyle=color;c.textAlign=align;c.fillText(str,x,y);};
    // Survey grid, fixed fiducials and technical rings.
    c.strokeStyle='#c5c7d0';c.lineWidth=.65;
    for(const delta of [-340,0,340]){c.beginPath();c.moveTo(C+delta,65);c.lineTo(C+delta,835);c.stroke();}
    for(const delta of [-340,0,340]){c.beginPath();c.moveTo(65,C+delta);c.lineTo(835,C+delta);c.stroke();}
    const bloom=c.createRadialGradient(C-140,C-20,150,C-80,C,350);bloom.addColorStop(0,'rgba(76,92,213,.14)');bloom.addColorStop(.62,'rgba(94,104,196,.05)');bloom.addColorStop(1,'rgba(94,104,196,0)');c.fillStyle=bloom;c.fillRect(40,40,820,820);
    circle(363,'#b3b6c5',.8);circle(357,'#b3b6c5',.8);circle(321,'#8f94a8',.75);circle(313,'#c8cbd3',1);circle(278,'#b8bbc9',.7);circle(250,'#b8bbc9',.7);
    circle(340,'#202538',3,Math.PI*1.07,Math.PI*1.38);circle(340,'#202538',3,-Math.PI*.30,Math.PI*.04);circle(340,'#303dbe',4,Math.PI*.24,Math.PI*.48);
    circle(302,'#303dbe',2,-Math.PI*.88,-Math.PI*.57);circle(291,'#d7d9e1',10,Math.PI*.08,Math.PI*.61);
    circle(237,'#1c253e',5,Math.PI*.92,Math.PI*1.40);circle(237,'#a5abc6',1.5,Math.PI*1.43,Math.PI*1.86);
    circle(237,'#b6573f',4,Math.PI*.12,Math.PI*.12+Math.max(.002,progress)*Math.PI*.61);
    for(let i=0;i<180;i++){const a=i/180*TAU-Math.PI/2,major=i%15===0;const r=major?347:352;c.beginPath();c.moveTo(C+Math.cos(a)*r,C+Math.sin(a)*r);c.lineTo(C+Math.cos(a)*357,C+Math.sin(a)*357);c.strokeStyle=major?'#31384f':'#a0a4b4';c.lineWidth=major?1.3:.7;c.stroke();}
    for(let i=0;i<12;i++){const a=i/12*TAU-Math.PI/2;text(String(i*30).padStart(3,'0'),C+Math.cos(a)*379,C+Math.sin(a)*379+4,10,'#6d7180');}
    // Fine orbital ellipse; this is an aesthetic frame, not an ephemeris.
    c.save();c.translate(C,C);c.rotate(-.35);c.beginPath();c.ellipse(0,0,402,150,0,0,TAU);c.strokeStyle='rgba(48,61,190,.27)';c.lineWidth=.8;c.stroke();c.restore();
    for(const [x,y] of [[110,110],[790,110],[110,790],[790,790]]){c.strokeStyle='#70788e';c.beginPath();c.moveTo(x-6,y);c.lineTo(x+6,y);c.moveTo(x,y-6);c.lineTo(x,y+6);c.stroke();}
    const angle=-Math.PI/2+progress*TAU,px=C+Math.cos(angle)*321,py=C+Math.sin(angle)*321;
    c.beginPath();c.arc(px,py,5,0,TAU);c.fillStyle='#303dbe';c.fill();c.beginPath();c.arc(px,py,10,0,TAU);c.strokeStyle='#303dbe55';c.stroke();
    text('N',450,43,11,'#303dbe');text('S',450,865,11);text('W',35,454,11);text('E',865,454,11);
    text('EARTH’S SHADOW',450,174,9,'#666c7e');text(`SAROS ${event.saros}`,450,739,10,'#5d6377');
    c.save();c.translate(153,450);c.rotate(-Math.PI/2);text('PENUMBRA / UMBRA',0,0,8);c.restore();
    c.save();c.translate(749,450);c.rotate(Math.PI/2);text('SELENOGRAPHIC STUDY',0,0,8);c.restore();
    // Shade the generated terrain with a moving, circular Earth shadow.
    const shadow=shadowAt(event,progress),pixels=this.image.data;
    for(const {idx,x,y} of this.disc){
      const distance=Math.hypot(x-shadow.x,y-shadow.y);
      const pen=clamp((shadow.penRadius-distance)/(shadow.penRadius-shadow.radius));
      const u=clamp((shadow.radius-distance)/.10+.5);
      const umbra=u*u*(3-2*u),base=this.terrain[idx],dim=1-.24*pen;
      const depth=clamp((shadow.radius-distance)/1.7);
      const red=base*(.65-.3*depth)+8,green=base*(.25-.15*depth)+3,blue=base*(.15-.06*depth)+6;
      pixels[idx*4]=base*dim*(1-umbra)+red*umbra;
      pixels[idx*4+1]=(base*dim+2)*(1-umbra)+green*umbra;
      pixels[idx*4+2]=(base*dim+8)*(1-umbra)+blue*umbra;
    }
    this.surfaceCtx.putImageData(this.image,0,0);
    const aura=c.createRadialGradient(C,C,184,C,C,233);aura.addColorStop(0,'rgba(36,41,67,.14)');aura.addColorStop(1,'rgba(36,41,67,0)');c.fillStyle=aura;c.beginPath();c.arc(C,C,233,0,TAU);c.fill();
    c.drawImage(this.surface, C-204,C-204,408,408);circle(205,'rgba(255,255,255,.5)',.7);
    // Leader lines tie the moon to the surrounding instrument.
    c.strokeStyle='#4e5879';c.lineWidth=.7;c.beginPath();c.moveTo(617,565);c.lineTo(686,624);c.lineTo(778,624);c.stroke();
    text('LUNA / 01',778,618,9,'#46516d','right');
    c.beginPath();c.arc(617,565,3,0,TAU);c.stroke();
    c.strokeStyle='#303dbe';c.strokeRect(85,348,13,13);text('γ '+event.gamma.toFixed(4),82,379,9,'#4e5879','left');
    text(String(Math.round(progress*100)).padStart(3,'0')+'%',793,514,12,'#303dbe');
  }
}
