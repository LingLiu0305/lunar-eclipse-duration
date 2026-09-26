import {TYPES,contactsFor,timeAt,formatTime,phaseAt} from './model.mjs';
import {Instrument} from './instrument.mjs';

const $=id=>document.getElementById(id);
const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
const state={records:[],year:2026,event:null,progress:0,playing:false,speed:1,offset:8,last:0,paint:0,contacts:[],phase:''};
let instrument;
function setPlaying(value){state.playing=value;$('play-label').textContent=value?'暂停':state.progress>=1?'再看一次':'播放';$('play-icon').textContent=value?'Ⅱ':'▶';$('play').setAttribute('aria-label',value?'暂停月食动画':'播放月食动画');updateStatus();}
function updateStatus(){if(!state.event)return;$('playback-status').textContent=`${state.playing?'正在播放':state.progress>=1?'本次播放结束':'已暂停'} · ${TYPES[state.event.type][0]} · 约 ${Math.round(60/state.speed)} 秒重现全程`;}
function renderClock(){
  const time=timeAt(state.event,state.progress),f=formatTime(time,state.offset);
  $('current-date').textContent=f.date;$('current-time').textContent=f.clock;
  $('timeline').value=String(Math.round(state.progress*1000));
  const phase=phaseAt(state.event,state.progress);
  $('timeline').setAttribute('aria-valuetext',`${f.date} ${f.clock}，${phase.name}`);
  $('phase-name').textContent=phase.name;$('phase-description').textContent=phase.description;$('phase-caption').textContent=phase.name;$('phase-code').textContent=phase.code;
  $('moon').setAttribute('aria-label',`${f.date} ${f.clock}，${TYPES[state.event.type][0]}，${phase.name}，艺术化示意`);
  let current=0;for(let i=0;i<state.contacts.length;i++)if(state.contacts[i].time<=time+1)current=i;
  [...$('contacts').children].forEach((button,i)=>{button.classList.toggle('is-current',i===current);if(i===current)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');});
}
function render(){if(!state.event)return;renderClock();instrument.draw(state.event,state.progress);}
function renderContacts(){
  const event=state.event,start=timeAt(event,0),end=timeAt(event,1);
  $('start-time').textContent=formatTime(start,state.offset).short;$('end-time').textContent=formatTime(end,state.offset).short;
  $('contacts').replaceChildren();$('contacts').style.setProperty('--contact-count',state.contacts.length);
  for(const point of state.contacts){
    const time=formatTime(point.time,state.offset),button=document.createElement('button');button.className='contact';
    button.setAttribute('aria-label',`跳转至${point.label}，${time.date} ${time.clock}${point.code==='MAX'?'':'，近似'}`);
    button.innerHTML=`<span class="contact-code">${point.code}</span><span class="contact-label">${point.label}</span><span class="contact-time">${point.code==='MAX'?'':'≈ '}${time.short}</span><span class="contact-day">${time.day}</span>`;
    button.addEventListener('click',()=>{state.progress=(point.time-start)/(end-start);setPlaying(false);render();});$('contacts').append(button);
  }
}
function chooseEvent(event,autoplay=true){
  state.event=event;state.progress=0;state.contacts=contactsFor(event);
  [...$('events').children].forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.id===event.id)));
  $('total-duration').innerHTML=event.totalMinutes==null?'—':`${event.totalMinutes.toFixed(1)} <small>min</small>`;
  $('total-duration').setAttribute('aria-label',event.totalMinutes==null?'本次无全食阶段':`全食持续 ${event.totalMinutes} 分钟`);
  $('magnitude').textContent=event.umbralMagnitude.toFixed(3);$('catalogue-id').textContent=`CAT. ${event.id}`;$('nasa-event').href=event.source;
  $('phase-bands').replaceChildren();
  for(const [minutes,className] of [[event.umbralMinutes,''],[event.totalMinutes,'total-band']])if(minutes!=null){const band=document.createElement('span');band.className=`phase-band ${className}`;band.style.left=`${(1-minutes/event.penumbralMinutes)*50}%`;band.style.width=`${minutes/event.penumbralMinutes*100}%`;$('phase-bands').append(band);}
  renderContacts();setPlaying(autoplay&&!motion.matches);render();
}
function chooseYear(year){
  state.year=Math.max(2001,Math.min(2100,Number(year)));$('year').value=String(state.year);
  const events=state.records.filter(row=>row.year===state.year);
  $('previous-year').disabled=state.year===2001;$('next-year').disabled=state.year===2100;
  $('event-count').textContent=`${String(events.length).padStart(2,'0')} EVENTS`;
  $('year-note').textContent=`${events.length} 次月食 · ${events.filter(e=>e.type==='T').length} 次月全食`;
  $('events').replaceChildren();
  for(const event of events){const button=document.createElement('button');button.className='event-button';button.dataset.id=event.id;
    const date=event.date.slice(5).replace('-',' / ');
    button.innerHTML=`<span class="event-moon ${event.type}" aria-hidden="true"></span><span><span class="event-date">${date}</span><span class="event-type">${TYPES[event.type][0]} / ${TYPES[event.type][1]}</span></span><span class="event-arrow" aria-hidden="true">↗</span>`;
    button.setAttribute('aria-label',`${event.date} ${TYPES[event.type][0]}，播放`);button.addEventListener('click',()=>chooseEvent(event));$('events').append(button);
  }
  chooseEvent(events[0]);
}
function tick(now){
  const dt=state.last?Math.min(now-state.last,100):0;state.last=now;
  if(state.playing&&state.event){state.progress=Math.min(1,state.progress+dt/60000*state.speed);if(now-state.paint>40||state.progress>=1){render();state.paint=now;}if(state.progress>=1)setPlaying(false);}
  requestAnimationFrame(tick);
}
async function init(){
  try{
    const response=await fetch('./eclipses.json');if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const records=await response.json();if(!Array.isArray(records)||records.length!==228)throw new Error('目录记录不完整');
    state.records=records;instrument=new Instrument($('moon'));
    $('year').replaceChildren();for(let year=2001;year<=2100;year++)$('year').add(new Option(String(year),String(year)));
    for(const id of ['year','play','replay','timeline'])$(id).disabled=false;
    chooseYear(2026);requestAnimationFrame(tick);
  }catch(error){$('load-error').hidden=false;$('load-error').textContent=`无法加载月食目录。请通过 uv run serve.py 启动本地页面，再刷新重试。${error.message}`;const retry=document.createElement('button');retry.textContent='重新加载';retry.addEventListener('click',()=>location.reload());$('load-error').append(retry);$('year-note').textContent='数据加载失败';$('phase-caption').textContent='等待数据';$('playback-status').textContent='未开始';}
}
$('year').addEventListener('change',event=>chooseYear(event.target.value));
$('previous-year').addEventListener('click',()=>{if(state.records.length)chooseYear(state.year-1);});
$('next-year').addEventListener('click',()=>{if(state.records.length)chooseYear(state.year+1);});
$('play').addEventListener('click',()=>{if(state.progress>=1)state.progress=0;setPlaying(!state.playing);render();});
$('replay').addEventListener('click',()=>{state.progress=0;setPlaying(true);render();});
$('timeline').addEventListener('input',event=>{state.progress=Number(event.target.value)/1000;setPlaying(false);render();});
$('timezone').addEventListener('change',event=>{state.offset=Number(event.target.value);if(state.event){renderContacts();render();}});
$('speed').addEventListener('change',event=>{state.speed=Number(event.target.value);updateStatus();});
motion.addEventListener('change',()=>{if(motion.matches)setPlaying(false);});
document.addEventListener('visibilitychange',()=>{if(document.hidden)setPlaying(false);});
init();
