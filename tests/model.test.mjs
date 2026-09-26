import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {contactsFor,timeAt,formatTime,phaseAt,shadowAt} from '../web/model.mjs';
const records=JSON.parse(readFileSync(new URL('../site/eclipses.json',import.meta.url)));

test('all contact orders and durations match the source, with no invented totality',()=>{
  for(const event of records){
    const points=contactsFor(event),byCode=Object.fromEntries(points.map(p=>[p.code,p.time]));
    assert.equal(points.length,{T:7,P:5,N:3}[event.type]);
    for(let i=1;i<points.length;i++)assert.ok(points[i].time>points[i-1].time);
    assert.ok(Math.abs((byCode.P4-byCode.P1)/60000-event.penumbralMinutes)<1e-6);
    if(event.type==='T')assert.ok(Math.abs((byCode.U3-byCode.U2)/60000-event.totalMinutes)<1e-6);
    assert.equal(timeAt(event,.5),event.greatestUT);
    assert.equal(phaseAt(event,.5).code,'MAX');
    assert.equal(phaseAt(event,1).code,'P4');
  }
});
test('clock offset and cross-midnight date are consistent',()=>{
  const t=Date.UTC(2026,2,3,20,15,30);
  assert.deepEqual(formatTime(t,8),{date:'2026.03.04',clock:'04:15:30',short:'04:15',day:'03/04'});
  assert.equal(formatTime(t,0).date,'2026.03.03');
});
test('partial eclipses do not describe an exit from totality',()=>{
  const partial=records.find(e=>e.date==='2026-08-28');
  assert.equal(phaseAt(partial,.55).name,'渐离本影');
});
test('shadow touches the lunar limb at contacts, clears it at endpoints, and follows magnitude',()=>{
  for(const event of records){
    const start=timeAt(event,0),span=event.penumbralMinutes*60000;
    for(const point of contactsFor(event)){
      const s=shadowAt(event,(point.time-start)/span),distance=Math.hypot(s.x,s.y);
      if(point.code==='P1'||point.code==='P4')assert.ok(Math.abs(distance-s.penRadius-1)<1e-5);
      if(point.code==='U1'||point.code==='U4')assert.ok(Math.abs(distance-s.radius-1)<1e-5);
      if(point.code==='U2'||point.code==='U3')assert.ok(Math.abs(distance-s.radius+1)<1e-5);
      if(point.code==='MAX')assert.ok(Math.abs((s.radius+1-distance)/2-event.umbralMagnitude)<1e-5);
    }
  }
});
