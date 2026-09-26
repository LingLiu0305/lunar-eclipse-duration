/** Catalogue times are UT milliseconds, not a claim of exact UTC. */
export const TYPES = {T: ['月全食', 'TOTAL'], P: ['月偏食', 'PARTIAL'], N: ['半影月食', 'PENUMBRAL']};
export function contactsFor(event) {
  const g = event.greatestUT;
  const points = [{code:'P1', label:'半影食始', time:g-event.penumbralMinutes*30000}];
  if (event.umbralMinutes != null) points.push({code:'U1',label:'初亏',time:g-event.umbralMinutes*30000});
  if (event.totalMinutes != null) points.push({code:'U2',label:'食既',time:g-event.totalMinutes*30000});
  points.push({code:'MAX',label:'食甚',time:g});
  if (event.totalMinutes != null) points.push({code:'U3',label:'生光',time:g+event.totalMinutes*30000});
  if (event.umbralMinutes != null) points.push({code:'U4',label:'复圆',time:g+event.umbralMinutes*30000});
  points.push({code:'P4',label:'半影食终',time:g+event.penumbralMinutes*30000});
  return points;
}
export function timeAt(event, progress) {return event.greatestUT + (Math.max(0,Math.min(1,progress))-.5)*event.penumbralMinutes*60000;}
export function formatTime(time, offset=8) {
  const d = new Date(time+offset*3600000);
  const iso = d.toISOString();
  return {date:iso.slice(0,10).replaceAll('-','.'),clock:iso.slice(11,19),short:iso.slice(11,16),day:iso.slice(5,10).replace('-','/')};
}
export function phaseAt(event, progress) {
  const minutes = (progress-.5)*event.penumbralMinutes;
  if (progress >= 1) return {code:'P4',name:'半影食终',description:'月亮已完全离开地球半影，本次月食结束。'};
  if (progress <= 0) return {code:'P1',name:'半影食始',description:'月亮开始进入地球半影，月面逐渐变暗。'};
  if (Math.abs(minutes)<.2) return {code:'MAX',name:'食甚',description:'月亮最接近地球影锥轴线，月食达到最深。'};
  if (event.totalMinutes != null && Math.abs(minutes)<=event.totalMinutes/2) return {code:minutes<0?'U2':'U3',name:'全食阶段',description:'整个月面进入本影，示意月球呈现暗铜红色。'};
  if (event.umbralMinutes != null && Math.abs(minutes)<=event.umbralMinutes/2) return {code:minutes<0?'U1':'U4',name:minutes<0?'初亏 · 渐入本影':event.totalMinutes!=null?'生光 · 渐离本影':'渐离本影',description:minutes<0?'地球本影缓缓掠过月面，明亮区域逐渐缩小。':'月球逐渐离开地球本影，明亮的月面重新显现。'};
  return {code:minutes<0?'P1':'P4',name:minutes<0?'进入半影':'离开半影',description:minutes<0?'月球进入较浅的半影，月面亮度轻微降低。':'月面逐渐恢复明亮，即将结束这次阴影之旅。'};
}

/** Schematic geometry, fitted to catalogue magnitude and symmetric contacts.
 * Distances are lunar radii; orientation and velocity are illustrative. */
export function shadowAt(event, progress) {
  const radius = Math.max(2.65, 2*event.umbralMagnitude-1+.04);
  const impact = radius+1-2*event.umbralMagnitude;
  const penRadius = radius+2*(event.penumbralMagnitude-event.umbralMagnitude);
  const chord = distance => Math.sqrt(Math.max(0,distance*distance-impact*impact));
  const nodes = [{minute:0,x:0}];
  if (event.totalMinutes != null) nodes.push({minute:event.totalMinutes/2,x:chord(radius-1)});
  if (event.umbralMinutes != null) nodes.push({minute:event.umbralMinutes/2,x:chord(radius+1)});
  nodes.push({minute:event.penumbralMinutes/2,x:chord(penRadius+1)});
  const elapsed=Math.abs(progress-.5)*event.penumbralMinutes;
  let x=nodes.at(-1).x;
  for(let i=1;i<nodes.length;i++) if(elapsed<=nodes[i].minute){
    const a=nodes[i-1],b=nodes[i];
    x=a.x+(b.x-a.x)*(elapsed-a.minute)/(b.minute-a.minute);break;
  }
  return {x:x*(progress<.5?-1:1),y:impact*(event.gamma<0?-1:1),radius,penRadius};
}
