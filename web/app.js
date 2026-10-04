'use strict';
  const $ = id => document.getElementById(id);
  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const shortDate = day => day ? `${Number(day.slice(8,10))} ${months[Number(day.slice(5,7))-1]}` : 'Unknown date';
  const fullDate = day => day ? `${shortDate(day)} ${day.slice(0,4)}` : 'Unknown date';
  const dateRange = window => window ? `${fullDate(window.start_date)} – ${fullDate(window.end_date)}` : 'Routine baseline visit';
  const timestamp = value => value ? value.replace('T',' ').replace(/Z$/, ' UTC') : 'retrieval time unavailable';
  const niceTime = value => value ? `${fullDate(value.slice(0,10))}, ${value.slice(11,16)} UTC` : 'time unknown';
  const boundaryText = storm => storm.next_day_status==='below threshold'
    ? `Rain fell below ${data.config.RAIN_MM} mm the next day. Daily totals don't show the exact hour it stopped.`
    : `There's no data for the following day, so we can't confirm when the rain stopped.`;
  const numeric = value => typeof value === 'number' && Number.isFinite(value);
  const displayedNumber = value => numeric(value) ? String(value) : 'Unknown';
  const scoreText = value => {
    if(!numeric(value)) return 'Unknown';
    const shown = value.toFixed(2);
    return Number(shown) === value ? shown : `${shown} (source ${value})`;
  };
  const link = (url,label) => {
    try { if (!['https:','http:'].includes(new URL(url).protocol)) throw new Error(); }
    catch { return escapeHTML(label); }
    return `<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(label)}</a>`;
  };
  const GUIDE_KEY='afterstorm-guide-seen-v1';
  const GUIDE_SUPPRESSED=new URLSearchParams(location.search).get('guide')==='0'||/^#(?:card|notice)-/.test(location.hash);
  const GUIDE_STEPS=[
    {title:'Choose the evidence',copy:'Pick a city and mode. Archive replay shows a real past storm; Latest forecast shows this week.',target:'#controlbar'},
    {title:'Read the answer',copy:'This is the answer: which streams to reassess after the storm, and when. Dates are an experimental window the coordinator confirms.',target:'#decision'},
    {title:'Review and hand off',copy:'Review here: approve or hold each visit and notice, open a citizen task card, then download the lab sheet or draft FHIR requests. Nothing is sent.',target:'.app-nav'}
  ];
  let guideIndex=0,guideReturn=null,guideTarget=null;
  function positionGuide(){
    const target=document.querySelector(GUIDE_STEPS[guideIndex].target);
    guideTarget?.classList.remove('guide-target');guideTarget=target;
    target?.classList.add('guide-target');
    if(!target||matchMedia('(max-width:760px)').matches) return;
    const rect=target.getBoundingClientRect(),width=Math.min(380,innerWidth-24);
    $('guide').style.setProperty('--guide-left',`${Math.max(12,Math.min(rect.left,innerWidth-width-12))}px`);
    $('guide').style.setProperty('--guide-top',`${Math.max(12,Math.min(rect.bottom+16,innerHeight-220))}px`);
  }
  function showGuideStep(){
    const step=GUIDE_STEPS[guideIndex];
    $('guide-step').textContent=`Step ${guideIndex+1} of ${GUIDE_STEPS.length}`;
    $('guide-title').textContent=step.title;$('guide-copy').textContent=step.copy;
    $('guide-back').hidden=guideIndex===0;$('guide-next').textContent=guideIndex===GUIDE_STEPS.length-1?'Done':'Next';
    positionGuide();$('guide-next').focus();
  }
  function closeGuide(){
    $('guide').hidden=true;guideTarget?.classList.remove('guide-target');guideTarget=null;
    try{localStorage.setItem(GUIDE_KEY,'1');}catch{}
    guideReturn?.focus({preventScroll:true});
  }
  function openGuide(opener){
    guideReturn=opener||$('open-guide');guideIndex=0;
    if(page!=='overview') goPage('overview');
    $('guide').hidden=false;showGuideStep();
  }
  function guideKeys(event){
    if($('guide').hidden) return;
    if(event.key==='Escape'){event.preventDefault();closeGuide();return;}
    if(event.key!=='Tab') return;
    const buttons=[...$('guide').querySelectorAll('button:not([hidden])')];
    const first=buttons[0],last=buttons.at(-1);
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  }
  let data, filed = null, cityId = 'OS', mode = 'live', budget = 5, leafletMap, tileLayer, markers = new Map();
  let markerGroup, previousMapCity, tileFailed = false, pins = new Map();

  function view(){const city=data.cities[cityId], plan=city.modes[mode];return {city,plan,allocated:new Set(plan.ranking.slice(0,budget))};}
  function planningStatus(site,allocated){
    if(site.status==='invalid source data') return {label:'Invalid source data',color:'#e0786d',kind:'excluded'};
    if(site.action==='first baseline assessment') return allocated.has(site.code) ? {label:'Baseline visit planned',color:'#3b82c4',kind:'baseline'} : {label:'Baseline · if capacity allows',color:'#d9a441',kind:'capacity'};
    if(site.action==='new category assessment') return allocated.has(site.code) ? {label:'Sample this storm',color:'#1f9d73',kind:'sample'} : {label:'If capacity allows',color:'#d9a441',kind:'capacity'};
    return {label:site.status,color:'#7d8f86',kind:'low'};
  }
  function rainChart(period){
    if(!period?.rain_mm_by_date) return '';
    const entries=Object.entries(period.rain_mm_by_date), max=Math.max(data.config.RAIN_MM,...entries.map(([,v])=>numeric(v)?v:0));
    const width=455,height=80,base=56,scale=40/max,step=width/entries.length;
    const threshold=base-data.config.RAIN_MM*scale;
    return `<svg class="rain-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Cached seven-day rainfall forecast in millimetres. Dashed line: ${escapeHTML(data.config.RAIN_MM)} mm storm threshold."><title>${escapeHTML(entries.map(([d,v])=>`${d}: ${displayedNumber(v)} mm`).join('; '))}</title><line x1="0" x2="${width}" y1="${threshold}" y2="${threshold}" stroke="#f2c46d" stroke-dasharray="3 3"/>${entries.map(([day,rain],i)=>{const wet=numeric(rain)&&rain>=data.config.RAIN_MM, h=numeric(rain)?Math.max(2,rain*scale):0;return `<rect x="${i*step+16}" y="${base-h}" width="${step-32}" height="${h}" rx="2" fill="${wet?'#6ee7b7':'#ffffff33'}"/><text x="${i*step+step/2}" y="${base-h-4}" text-anchor="middle" font-family="Geist,Segoe UI,system-ui,sans-serif" font-size="11.5" fill="${wet?'#6ee7b7':'#9db3a9'}">${numeric(rain)&&rain>0?escapeHTML(rain):numeric(rain)?'':'?'}</text><text x="${i*step+step/2}" y="76" text-anchor="middle" font-family="Geist,Segoe UI,system-ui,sans-serif" font-size="11.5" fill="#9db3a9">${escapeHTML(shortDate(day))}</text>`;}).join('')}</svg>`;
  }
  function siteRainChart(plan){
    const storm=plan.storm; if(!storm?.rain_mm_by_site_by_date) return '';
    const day=storm.anchor_date, entries=Object.entries(storm.rain_mm_by_site_by_date).map(([c,d])=>[c,d[day]]).filter(([,v])=>numeric(v)).sort((x,y)=>y[1]-x[1]);
    const max=Math.max(data.config.RAIN_MM,...entries.map(([,v])=>v)),width=455,height=96,base=70,scale=58/max,step=width/entries.length,thr=base-data.config.RAIN_MM*scale;
    return `<svg class="rain-chart tall" viewBox="0 0 ${width} ${height}" role="img" aria-label="Rain at each of ${entries.length} sites on ${escapeHTML(day)}; every bar is above the ${data.config.RAIN_MM} mm line."><title>${escapeHTML(entries.map(([c,v])=>`${c}: ${v} mm`).join('; '))}</title>${entries.map(([c,v],i)=>{const h=Math.max(2,v*scale);return `<rect x="${i*step+step*.18}" y="${base-h}" width="${step*.64}" height="${h}" rx="2" fill="#6ee7b7"/><text x="${i*step+step/2}" y="86" text-anchor="middle" font-family="Geist Mono,monospace" font-size="${entries.length>16?8:10}" fill="#9db3a9">${escapeHTML(c)}</text>`;}).join('')}<line x1="0" x2="${width}" y1="${thr}" y2="${thr}" stroke="#f2c46d" stroke-dasharray="4 3"/></svg>`;
  }
  function renderWeather(city,plan,allocated){
    const storm=plan.storm;
    const unknown=plan.weather_status==='unknown';
    const tag=unknown?'Rain data incomplete':storm?(mode==='live'?'Storm forecast':'Past storm'):'No storm forecast';
    const baseline=plan.sites.filter(s=>s.action==='first baseline assessment').length;
    const why=unknown?`Rain data for ${escapeHTML(city.name)} is incomplete, so a storm can't be ruled out. Only visits to streams with no lab result in the public feed are planned.`
      :storm?`<strong>${escapeHTML(boundaryText(storm))}</strong> A day with ${data.config.RAIN_MM} mm of rain or more triggers a plan. What's in the water is unknown until it's sampled.`
      :mode==='live'?`No day in the next week reaches ${data.config.RAIN_MM} mm, so there's no storm sampling to plan.${baseline?' Streams with no lab result in the public feed are still listed.':''}`:escapeHTML(plan.message);
    const rule=(mode==='live'?'One forecast covers the whole city, so every site shares the same storm day.':`A past day qualifies only if <strong>every</strong> site in the city had ${data.config.RAIN_MM} mm or more. Days with missing data are never counted as dry or wet.`)+' 20 mm in a day is the WMO/ETCCDI “very heavy precipitation day” index (R20mm), used here as a prototype setting.';
    const chart=mode==='live'?rainChart(plan.forecast_period):siteRainChart(plan);
    const caption=mode==='live'?`Daily rain forecast for ${escapeHTML(city.name)}, mm. Dashed line: ${data.config.RAIN_MM} mm.`:storm?`Rain at every ${escapeHTML(city.name)} site on ${escapeHTML(fullDate(storm.anchor_date))}, mm, highest first. Dashed line: ${data.config.RAIN_MM} mm storm line.`:'';
    $('weather').innerHTML=`<div class="weather-top"><h2>Rain evidence · ${escapeHTML(city.name)}</h2><span class="badge ${mode==='replay'?'replay':''}">${escapeHTML(tag)}</span></div><div class="weather-bottom"><div class="weather-explain"><p>${why}</p><p style="margin-top:10px">${rule}</p></div><figure class="chart-fig">${chart||'<p class="weather-explain">No rain chart for this view.</p>'}${caption?`<figcaption>${caption}</figcaption>`:''}</figure></div>`;
    $('replay-banner').hidden=mode!=='replay';
    const sentence=demonstrationSentence();
    const liveStorm=!!data.cities[cityId].modes.live.storm;
    $('replay-banner').innerHTML=storm?`<div class="rc-text"><strong>Replay of a real storm · ${escapeHTML(fullDate(storm.anchor_date))}</strong><span>You're seeing what AfterStorm would have planned the day after this storm, using real past data. ${liveStorm?'A storm is also forecast this week.':'No heavy rain is forecast this week.'}</span>${sentence?`<span class="demo-line">Filed to the HL7 sandbox as: ${escapeHTML(sentence)}</span>`:''}</div><button type="button" class="rc-btn" data-mode-live>See latest forecast →</button>`:`<div class="rc-text"><strong>Replay</strong><span>No past storm in the archive reached the trigger at every site in this city.</span></div><button type="button" class="rc-btn" data-mode-live>See latest forecast →</button>`;
  }
  function sourceDetails(site,plan){
    const health=site.source_health;
    const rain=plan.storm?(mode==='live'?plan.storm.rain_mm_by_date[plan.storm.anchor_date]:plan.storm.rain_mm_by_site_by_date[site.code][plan.storm.anchor_date]):null;
    const fields=health?`<dt>Lab sample date (samplingDate)</dt><dd>${escapeHTML(site.sample_date)}</dd><dt>Faecal (scaledFecalRisk)</dt><dd>${escapeHTML(scoreText(health.scaledFecalRisk))}</dd><dt>Pathogen (scaledPathogenRisk)</dt><dd>${escapeHTML(scoreText(health.scaledPathogenRisk))}</dd><dt>Antibiotic resistance (scaledArgRisk)</dt><dd>${escapeHTML(scoreText(health.scaledArgRisk))}</dd>`:'<dt>Lab evidence</dt><dd>No lab result</dd>';
    return `<details class="why" data-keep="why-${escapeHTML(site.code)}"><summary>Why?</summary><div class="sheet-panel" role="dialog" aria-label="Why ${escapeHTML(site.code)} is in the plan"><div class="sheet-head"><span>Why this site · <strong>${escapeHTML(site.code)} ${escapeHTML(site.name)}</strong></span><button type="button" class="sheet-close" data-close-sheet aria-label="Close">×</button></div><p class="reason">${escapeHTML(site.reason)}</p><dl class="source-fields">${fields}<dt>Sewage distance (distanceToSewageStations)</dt><dd>${numeric(site.sewage_distance_m)?escapeHTML(site.sewage_distance_m)+' m':'Missing; last among baselines'}</dd>${plan.storm?`<dt>${mode==='live'?'City forecast rain':'Archived site rain'} on ${escapeHTML(plan.storm.anchor_date)}</dt><dd>${escapeHTML(displayedNumber(rain))} mm</dd>`:''}</dl>${site.window?`<p class="reason">${escapeHTML(site.window.why)} ${link(site.window.source,'Directive context')}</p>`:''}<details class="provenance"><summary>Source URLs and retrieval times</summary>${Object.entries(site.provenance).map(([name,ref])=>`<p>${link(ref.url,name==='rain'?(mode==='live'?'City forecast':'Site rainfall archive'):name==='health'?'Lab category results':name==='urban'?'Urban parameters':'Official roster')}<br>Fetched <span class="mono">${escapeHTML(timestamp(ref.fetched_at))}</span></p>`).join('')}</details></div></details>`;
  }
  let lastHeroKey='';
  function miniBars(values,threshold){
    const vals=values.filter(numeric); if(!vals.length) return '';
    const max=Math.max(threshold*1.15,...vals),w=220,h=46,step=w/vals.length,thr=h-threshold/max*h;
    return `<svg class="mini-bars" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">${vals.map((v,i)=>{const bh=Math.max(1.5,v/max*h);return `<rect x="${i*step+step*.2}" y="${h-bh}" width="${step*.6}" height="${bh}" rx="1.5" fill="${v>=threshold?'#6ee7b7':'#ffffff40'}"/>`;}).join('')}<line x1="0" x2="${w}" y1="${thr}" y2="${thr}" stroke="#f2c46d" stroke-width="1" stroke-dasharray="3 3" vector-effect="non-scaling-stroke"/></svg>`;
  }
  function calTile(day){return `<span class="cal-tile"><b>${months[Number(day.slice(5,7))-1].toUpperCase()}</b><span>${Number(day.slice(8,10))}</span></span>`;}
  function countUp(root){
    if(matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    root.querySelectorAll('[data-count]').forEach(el=>{
      const target=Number(el.dataset.count),dec=(el.dataset.count.split('.')[1]||'').length,t0=performance.now();
      const tick=now=>{const k=Math.min(1,(now-t0)/700),e=1-Math.pow(1-k,3);el.textContent=(target*e).toFixed(dec);if(k<1)requestAnimationFrame(tick);};
      requestAnimationFrame(tick);
    });
  }
  function renderDecision(city,plan,allocated){
    const storm=plan.storm, n=allocated.size, notices=plan.notices.length, RAIN=data.config.RAIN_MM;
    const sites=new Map(plan.sites.map(s=>[s.code,s]));
    const picked=plan.ranking.slice(0,budget).map(c=>sites.get(c));
    const baselines=picked.filter(s=>s.action==='first baseline assessment').length, stormVisits=n-baselines;
    const allBaselines=plan.sites.filter(s=>s.action==='first baseline assessment').length;
    const b=t=>`<strong>${escapeHTML(t)}</strong>`, plural=(k,w)=>`${k} ${w}${k===1?'':'s'}`;
    let answer, s1, s2, s3;
    if(plan.weather_status==='unknown'){
      const second=n?'Only visits to streams with no lab result in the public feed are planned.'
        :'Only visits to streams with no lab result in the public feed are planned, and none are needed.';
      answer=`Rain data for ${b(city.name)} is incomplete, so a storm can't be ruled out. ${second}`;
      s1='Rain data incomplete';
    }else if(storm){
      const when=mode==='live'?`Heavy rain is forecast for ${b(city.name)} on ${b(fullDate(storm.anchor_date))}.`:`Replay: heavy rain hit ${b(city.name)} on ${b(fullDate(storm.anchor_date))}.`;
      const win=`${shortDate(storm.window.start_date)} – ${shortDate(storm.window.end_date)}`;
      answer=n?`${when} Plan post-storm reassessment at ${b(plural(n,'stream'))} on ${b(win)} (dates to confirm)${baselines?` (including ${plural(baselines,'first sample')})`:''}.${notices?` ${b(plural(notices,'contact notice'))} ${notices===1?'needs':'need'} your review.`:''}`
              :`${when} ${budget===0?'Your visit budget is 0, so no visits are planned.':'No stream meets the threshold for a new test.'}`;
      s1=mode==='live'?`Forecast · ${shortDate(storm.anchor_date)}`:`Past storm · ${shortDate(storm.anchor_date)}`;
    }else{
      const nothing=mode==='live'?`No storm is forecast for ${b(city.name)} this week.`:`No past storm reached ${RAIN} mm at every ${escapeHTML(city.name)} site.`;
      answer=n?`${nothing} Use the quiet week to take ${b(plural(n,'first sample'))} at streams with no lab result in the public feed.`
              :`${nothing} ${budget===0&&allBaselines?`Your visit budget is 0; ${plural(allBaselines,'stream')} still ${allBaselines===1?'needs':'need'} a first assessment.`:allBaselines?`${plural(allBaselines,'stream')} ${allBaselines===1?'needs':'need'} a first assessment, but no visit is allocated.`:'Every stream has a lab result in the public feed, so no visit is proposed.'}${mode==='live'?' Check again after the next forecast update.':''}`;
      s1=mode==='live'?'No storm this week':'No qualifying storm';
    }
    s2=n?`${n} of ${budget} visits used${stormVisits&&baselines?` · ${baselines} first samples`:''}`:'Nothing to plan';
    const t=reviewTally(plan);
    s3=!n&&!notices?'Nothing to file':t.done===t.total?`All ${t.total} reviewed · ready to download`:`${t.done} of ${t.total} reviewed`;
    const state=['done', n?'done':'current', !(n||notices)?'todo':t.done===t.total?'done':'current'];
    const steps=[['Storm',s1,'weather'],['Plan visits',s2,'visit-panel'],['Review & file',s3,'review-progress']];
    // KPI tiles
    let rainVal,rainUnit='mm',rainLabel,rainSub,bars;
    if(plan.weather_status==='unknown'){rainLabel='Rain data';rainVal='?';rainUnit='';rainSub='Some days have no data; they are never counted as dry';bars='';}
    else if(storm&&mode==='live'){const v=storm.rain_mm_by_date[storm.anchor_date];rainLabel='Heavy rain forecast';rainVal=`<span data-count="${v}">${v}</span>`;rainSub=`${fullDate(storm.anchor_date)} · storm line ${RAIN} mm`;bars=miniBars(Object.values(plan.forecast_period?.rain_mm_by_date||{}),RAIN);}
    else if(storm){const r=storm.rain_range_mm_by_date[storm.anchor_date];rainLabel='Rain that day, every site';rainVal=r.min===r.max?`<span data-count="${r.min}">${r.min}</span>`:`<span data-count="${r.min}">${r.min}</span><span class="kpi-dash">–</span><span data-count="${r.max}">${r.max}</span>`;rainSub=`${fullDate(storm.anchor_date)} · all ${Object.keys(storm.rain_mm_by_site_by_date).length} sites above ${RAIN} mm`;bars=miniBars(Object.values(storm.rain_mm_by_site_by_date).map(d=>d[storm.anchor_date]).sort((x,y)=>y-x),RAIN);}
    else if(mode==='live'&&plan.forecast_period){const vals=Object.values(plan.forecast_period.rain_mm_by_date).filter(numeric),mx=vals.length?Math.max(...vals):0;rainLabel='Wettest day this week';rainVal=`<span data-count="${mx}">${mx}</span>`;rainSub=`Below the ${RAIN} mm storm line · no storm`;bars=miniBars(vals,RAIN);}
    else{rainLabel='Past rain';rainVal='—';rainUnit='';rainSub=`No day reached ${RAIN} mm at every site`;bars='';}
    const dateTile=plan.weather_status==='unknown'?`<div class="kpi-value small">${allBaselines?'Any day':'?'}</div><p class="kpi-sub">${allBaselines?`${plural(allBaselines,'stream')} with no public lab result`:'Rain data is incomplete, so no sampling window is set'}</p>`
      :storm?`<div class="cal">${calTile(storm.window.start_date)}<span class="cal-arrow" aria-hidden="true">→</span>${calTile(storm.window.end_date)}</div><span class="window-tag">Experimental window (heuristic, not validated)</span><p class="kpi-sub">The coordinator confirms the dates. Some contaminants peak during the storm itself; this window is a post-storm reassessment, not peak sampling.</p>`
      :`<div class="kpi-value small">${allBaselines?'Any day':'—'}</div><p class="kpi-sub">${allBaselines?`${plural(allBaselines,'stream')} with no public lab result · no storm timing needed`:'No storm, so no sampling window'}</p>`;
    const pct=budget?Math.min(100,n/budget*100):0;
    const ring=`<svg class="ring" viewBox="0 0 84 84" aria-hidden="true"><circle cx="42" cy="42" r="36" pathLength="100" class="ring-bg"/><circle cx="42" cy="42" r="36" pathLength="100" class="ring-fg" style="stroke-dashoffset:${100-pct}"/></svg>`;
    const kicker=mode==='live'?`<span class="pulse${storm&&plan.weather_status!=='unknown'?' warn':''}"></span>Latest saved forecast · fetched ${escapeHTML(niceTime(data.sources[`forecasts/${cityId}.json`]?.fetched_at))}`:'';
    $('decision').innerHTML=`${kicker?`<p class="hero-kicker">${kicker}</p>`:''}<h1 class="decision-answer" id="decision-answer">${answer}</h1>
      <div class="kpis">
        <div class="kpi"><p class="kpi-label">${escapeHTML(rainLabel)}</p><div class="kpi-value">${rainVal}${rainUnit?`<span class="kpi-unit">${rainUnit}</span>`:''}</div>${bars}<p class="kpi-sub">${escapeHTML(rainSub)}</p></div>
        <div class="kpi"><p class="kpi-label">${storm&&plan.weather_status!=='unknown'?'Proposed reassessment dates':'Sampling window'}</p>${dateTile}</div>
        <div class="kpi kpi-ring"><div class="ring-wrap">${ring}<span class="ring-num"><span data-count="${n}">${n}</span><small>of ${budget}</small></span></div><div><p class="kpi-label">Site visits</p><p class="kpi-big-sub">${n?plural(n,'stream'):'No visits'}</p><p class="kpi-sub">${plan.ranking.length} qualify${allBaselines?` · ${allBaselines} with no public lab result`:''}<br>One trip covers every test at a site</p></div></div>
      </div>
      <nav aria-label="Plan progress"><ol class="steps">${steps.map(([title,status,target],i)=>`<li class="step ${state[i]}"><button type="button" data-jump="${target}" ${state[i]==='current'?'aria-current="step"':''}><span class="step-dot" aria-hidden="true">${state[i]==='done'?'<svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>':i+1}</span><span class="step-text"><span class="step-title">${escapeHTML(title)}</span><span class="step-status">${escapeHTML(status)}</span></span><span class="step-go" aria-hidden="true">→</span></button></li>`).join('')}</ol></nav>`;
    $('hero').classList.toggle('storm',!!storm&&plan.weather_status!=='unknown');$('hero').classList.toggle('replay',mode==='replay');
    const key=`${cityId}|${mode}`; if(key!==lastHeroKey){lastHeroKey=key;countUp($('decision'));document.querySelectorAll('.visit-card').forEach((c,i)=>{c.classList.remove('enter');void c.offsetWidth;c.style.setProperty('--i',i);c.classList.add('enter');});}
    // city pills: pressed state + storm marker for the current mode
    $('city-pills').querySelectorAll('[data-city]').forEach(btn=>{const id=btn.dataset.city,modePlan=data.cities[id].modes[mode],has=modePlan.weather_status!=='unknown'&&!!modePlan.storm;btn.setAttribute('aria-pressed',String(id===cityId));btn.classList.toggle('has-storm',has);btn.title=modePlan.weather_status==='unknown'?'Rain data incomplete':has?(mode==='live'?'Storm in the latest saved forecast':'Past storm available'):'No storm';});
  }
  const PAGES=['overview','plan','notices','evidence'];
  const PAGE_OF={weather:'evidence',coverage:'evidence',roster:'evidence',sources:'evidence','visit-panel':'plan','review-progress':'plan',tracker:'plan',map:'plan','notice-panel':'notices',protection:'overview',hero:'overview'};
  let page='overview';
  function pageFromHash(){
    const h=location.hash;
    if(h.startsWith('#card-')) return 'plan';
    if(h.startsWith('#notice-')) return 'notices';
    if(!h||h==='#'||h==='#/') return 'overview';
    const m=h.match(/^#\/([a-z]+)/);
    return m&&PAGES.includes(m[1])?m[1]:page;
  }
  function setPage(next,{scroll=true}={}){
    page=next;document.body.dataset.page=next;
    document.querySelectorAll('.page').forEach(el=>el.classList.toggle('active',el.dataset.page===next));
    document.querySelectorAll('[data-page-link]').forEach(a=>{if(a.dataset.pageLink===next)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    if(next==='plan'&&leafletMap) requestAnimationFrame(()=>{leafletMap.invalidateSize();previousMapCity=null;const v=view();renderMap(v.city,v.plan,v.allocated);});
    if(scroll) window.scrollTo({top:0});
  }
  function goPage(next){
    if(next===page) return;
    history.pushState(null,'',`${location.search}${next==='overview'?'#/':'#/'+next}`);
    setPage(next);
  }
  function jumpTo(id){
    const target=PAGE_OF[id];
    if(target&&target!==page){goPage(target);requestAnimationFrame(()=>jumpTo(id));return;}
    const el=$(id); if(!el) return;
    const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({behavior:reduce?'instant':'smooth',block:'start'});
    el.focus({preventScroll:true});
    el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
  }
  const CAT_FIELD={'faecal':'scaledFecalRisk','pathogen':'scaledPathogenRisk','antibiotic resistance':'scaledArgRisk'};
  const CAT_CLASS={'faecal':'c-fec','pathogen':'c-path','antibiotic resistance':'c-arg'};
  function catChips(site){
    if(site.action==='first baseline assessment'){
      return `<span class="chip c-base">First baseline · no public lab result</span>`+site.categories.map(c=>`<span class="chip ${CAT_CLASS[c]||''} ghost">${escapeHTML(c)}</span>`).join('');
    }
    return site.categories.map(c=>{
      const v=site.source_health?.[CAT_FIELD[c]];
      const shown=numeric(v)?Number(v).toFixed(2):'?';
      const pct=numeric(v)?Math.max(4,Math.min(100,v*100)):0;
      return `<span class="chip ${CAT_CLASS[c]||''}" title="Stored ${escapeHTML(site.sample_date?.slice(0,4)||'')} relative score ${shown} (not a concentration)">${escapeHTML(c)} <b>${shown}</b><i class="meter" aria-hidden="true"><i style="width:${pct}%"></i></i></span>`;
    }).join('');
  }
  // Tremor-style tracker: one segment per site, ranked first, coloured by planning status.
  function renderTracker(plan,allocated){
    const el=$('tracker'); if(!el) return;
    const ranked=plan.ranking.map(c=>plan.sites.find(s=>s.code===c)).filter(Boolean);
    const rest=plan.sites.filter(s=>!plan.ranking.includes(s.code));
    const order=[...ranked,...rest];
    const counts={};
    const segs=order.map(site=>{
      const st=planningStatus(site,allocated);counts[st.kind]=(counts[st.kind]||0)+1;
      const label=`${site.code} ${site.name} · ${st.label}${site.draft_notice?' · draft notice':''}`;
      return `<button type="button" class="seg k-${st.kind}${site.draft_notice?' has-notice':''}" data-seg="${escapeHTML(site.code)}" title="${escapeHTML(label)}" aria-label="${escapeHTML(label)}"></button>`;
    }).join('');
    const legend=[['sample','planned storm visit'],['baseline','planned first sample'],['capacity','if capacity allows'],['low','no visit'],['excluded','excluded']].filter(([k])=>counts[k]).map(([k,l])=>`<span><i class="seg-dot k-${k}"></i>${counts[k]} ${l}</span>`).join('');
    el.innerHTML=`<div class="tracker-head"><strong>All ${plan.sites.length} ${escapeHTML(data.cities[cityId].name)} sites at a glance</strong><span>ranked first · ring = draft notice</span></div><div class="tracker-bar" role="group" aria-label="Planning status of every site">${segs}</div><div class="tracker-legend">${legend}</div>`;
  }
  function renderSummaryBar(city,plan,allocated){
    const t=reviewTally(plan),storm=plan.storm;
    const when=storm?(mode==='live'?`Storm forecast ${shortDate(storm.anchor_date)}`:'Past storm'):(mode==='live'?'No storm this week':'No qualifying storm');
    const pct=t.total?Math.round(t.done/t.total*100):0;
    $('header-status').innerHTML=`<div class="sb-inner"><strong>${escapeHTML(city.name)}</strong><span class="sb-tag${mode==='replay'?' replay':''}">${escapeHTML(when)}</span><span>${allocated.size} of ${budget} visits</span>${t.total?`<span class="sb-review"><i style="width:${pct}%"></i></span><span>${t.done}/${t.total} reviewed</span>`:''}<span class="sb-actions"><button type="button" data-sb-download${$('download-fhir').disabled?' disabled':''}>${escapeHTML($('download-fhir').textContent)}</button><button type="button" class="sb-secondary" data-sb-lab>Lab sheet (CSV)</button></span></div>`;
  }
  function renderNext(city,plan,allocated){
    const t=reviewTally(plan),n=allocated.size,notices=plan.notices.length;
    const items=[
      ['plan',`${n?`Review ${n} planned visit${n===1?'':'s'}`:'No visits planned'}`,n?'Map, ranked visits, citizen task cards and the FHIR download.':'See every site on the map and the full roster.'],
      ['notices',notices?`${notices} draft contact notice${notices===1?'':'s'}`:'No draft notices',notices?'Approve or hold each notice and set its confirmation sample date.':'Notices are drafted only for a storm scenario.'],
      ['evidence','Rain evidence and data','The rain chart, how often storms like this happen, sources, settings and the full roster.']];
    $('next-card').innerHTML=`<div class="panel-header"><div><h2 id="next-heading">Next steps</h2><p>${t.total?`${t.done} of ${t.total} items reviewed`:'Nothing to review in this view'}</p></div></div><div class="next-list">${items.map(([pg,title,sub])=>`<a class="next-item" href="${pg==='overview'?'#/':'#/'+pg}"><span><strong>${escapeHTML(title)}</strong><small>${escapeHTML(sub)}</small></span><span class="next-go" aria-hidden="true">→</span></a>`).join('')}</div>`;
    $('nav-notice-count').textContent=notices?String(notices):'';
  }
  function renderVisits(plan,allocated){
    const sites=new Map(plan.sites.map(s=>[s.code,s]));
    const selected=plan.ranking.slice(0,budget).map(code=>sites.get(code));
    $('visit-count').textContent=`${selected.length} planned`;
    $('visit-subtitle').textContent=plan.storm?'Within the experimental post-rain window':'Routine baseline visits where lab evidence is missing';
    if(selected.length){
      $('visits').innerHTML=`<ol class="visit-list">${selected.map(site=>`<li class="visit-card rv-${reviewOf('visit',site.code)||'none'}" id="visit-${escapeHTML(site.code)}" data-code="${escapeHTML(site.code)}"><div class="vr-grid"><span class="rank-number">${site.rank}</span><div class="vr-main"><h3><code>${escapeHTML(site.code)}</code>${escapeHTML(site.name)}</h3><p class="category-text">${catChips(site)}</p><p class="visit-time"><strong>${escapeHTML(dateRange(site.window))}</strong>${site.window?'<span class="small-window">Experimental window (heuristic, not validated)</span>':'<span class="small-window">No storm window</span>'}</p>${filedLine(site.code)}${reviewNote('visit',site.code)}${site.action==='first baseline assessment'&&site.sewage_distance_m===null?'<p class="distance-note">Missing sewage distance · last among baseline sites</p>':''}${site.map_note?`<p class="reason muted small">${escapeHTML(site.map_note)}</p>`:''}</div><div class="vr-side">${reviewButtons('visit',site.code,site.code+' '+site.name)}<div class="vr-links">${citizenCard(site)}${sourceDetails(site,plan)}${site.position?`<button type="button" class="locate" data-locate="${escapeHTML(site.code)}" aria-label="Show ${escapeHTML(site.code)} on map">Map</button>`:''}</div></div></div></li>`).join('')}</ol>`;
    }else{
      let reason;
      if(budget===0) reason='The site-visit budget is zero. Increase it to allocate eligible visits; the full roster and evidence remain available.';
      else if(plan.weather_status==='no_storm'&&!plan.sites.some(s=>s.action==='first baseline assessment')) reason='No storm is forecast in the cached seven-day period, and every site already has a lab result. No visits are planned.';
      else if(plan.weather_status==='unknown') reason='Rain evidence is incomplete, so storm visits are not scheduled. No valid baseline site is available for a routine visit; review the roster and source-data exclusions.';
      else if(plan.storm) reason='No valid site meets the configured assessment threshold, and there are no baseline sites awaiting a first assessment. No visits are planned; review the full roster below.';
      else reason='No complete city-wide archived storm qualifies, and no baseline site is awaiting a first assessment. No visits are planned.';
      $('visits').innerHTML=`<p class="empty-visits" id="empty-visits"><strong>No visits planned</strong>${escapeHTML(reason)}</p>`;
    }
    $('print-all-cards').disabled=!selected.length;
    const remaining=plan.ranking.slice(budget).map(code=>sites.get(code));
    $('capacity').innerHTML=remaining.length?`<details class="capacity-details"><summary>${remaining.length} more site${remaining.length===1?'':'s'} if capacity allows</summary>${remaining.map(s=>`<div class="capacity-row"><code>${escapeHTML(s.code)}</code><p>${escapeHTML(s.name)}<small>${s.action==='first baseline assessment'?'First baseline · ':''}${escapeHTML(s.categories.join(' + '))}${s.sewage_distance_m===null?' · missing sewage distance; last among baselines':''}</small></p>${s.position?`<button type="button" class="locate" data-locate="${escapeHTML(s.code)}" aria-label="Show ${escapeHTML(s.code)} on map">Show on map</button>`:''}</div>`).join('')}</details>`:'';
    updateFhirChrome(selected);
  }
  function updateFhirChrome(selected){
    const saved=data.fhir?.default_bundle, savedCity=saved&&data.cities[saved.city];
    if(savedCity){
      $('default-fhir').textContent=`Saved file: ${savedCity.name} ${saved.mode==='live'?'latest saved forecast':'REPLAY'}, budget ${saved.budget}`;
      $('default-fhir').download=`afterstorm-${saved.city}-${saved.mode}-budget-${saved.budget}.json`;
    }
    const sendable=selected.filter(site=>reviewOf('visit',site.code)!=='hold'),held=selected.length-sendable.length;
    const ready=sendable.length>0&&sendable.every(site=>site.service_request&&site.service_request_full_url);
    $('download-fhir').disabled=!ready;
    $('download-fhir').textContent=sendable.length?`Download FHIR (${sendable.length})`:'Download FHIR';
    if(!selected.length) $('fhir-status').textContent='No visits are in this list, so there is nothing to download.';
    else if(!sendable.length) $('fhir-status').textContent='Every visit is on hold, so there is nothing to download.';
    else if(!ready) $('fhir-status').textContent='The FHIR requests are missing. Run python plan.py, then reload.';
    else $('fhir-status').innerHTML=`<span class="fs-line"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>${sendable.length} draft request${sendable.length===1?'':'s'} ready${held?` · ${held} on hold left out`:''} · nothing is sent</span>${filedChip()}`;
  }
  function demonstrationSentence(){
    const demo=data.fhir?.demonstration;
    if(!demo||demo.city!==cityId||demo.mode!==mode||!demo.statement) return '';
    return demo.statement;
  }
  function filedMatches(){
    return !!(filed&&filed.city===cityId&&filed.mode===mode&&Array.isArray(filed.resources));
  }
  function filedLine(code){
    if(!filedMatches()) return '';
    const item=filed.resources.find(row=>row.code===code&&row.id);
    return item?`<p class="filed-note">Filed as FHIR ServiceRequest/${escapeHTML(item.id)} (filed with resource shape v1)</p>`:'';
  }
  function filedChip(){
    if(!filedMatches()) return '';
    const shown=filed.resources.filter(item=>item.id);
    if(!shown.length) return '';
    const base=String(filed.sandbox||'').replace(/\/$/,'');
    const when=filed.posted_at?niceTime(filed.posted_at):'';
    return `<details class="filed-chip"><summary>Filed once to the HL7 Europe sandbox · ServiceRequest ${escapeHTML(shown[0].id)}–${escapeHTML(shown.at(-1).id)} · shape v1</summary><ul>${shown.map(item=>`<li><code>${escapeHTML(item.code)}</code> → ${link(`${base}/ServiceRequest/${item.id}`,`ServiceRequest/${item.id}`)}</li>`).join('')}</ul><p>Filed as drafts${when?` on ${escapeHTML(when)}`:''} for this replay demonstration. The current export uses resource shape v2 (one request-type code, categories in orderDetail).</p></details>`;
  }
  function filedSummary(){
    if(!filedMatches()) return '';
    const shown=filed.resources.filter(item=>item.id);
    if(!shown.length) return '';
    return ` Already filed once to the HL7 Europe sandbox as drafts (filed with resource shape v1): ${shown.map(item=>`${item.code} → ServiceRequest ${item.id}`).join(', ')}.`;
  }
  const REVIEW_KEY='afterstorm-review-v2';
  let reviews={};try{reviews=JSON.parse(localStorage.getItem(REVIEW_KEY))||{};}catch{reviews={};}
  const rkey=(kind,code)=>`${cityId}|${mode}|${kind}|${code}`;
  function evidenceSig(kind,code){
    const {plan}=view(), storm=plan.storm;
    if(kind==='visit'){
      const site=plan.sites.find(s=>s.code===code)||{};
      return [storm?.anchor_date||'no-storm', site.action||'', (site.categories||[]).join('+'), site.window?`${site.window.start_date}/${site.window.end_date}`:'no-window', site.sample_date||'no-lab'].join('|');
    }
    const notice=(plan.notices||[]).find(n=>n.code===code)||{};
    return [storm?.anchor_date, notice.basis, notice.text].join('|');
  }
  function reviewOf(kind,code){
    const stored=reviews[rkey(kind,code)];
    if(!stored||typeof stored!=='object'||!stored.decision) return null;
    return stored.sig===evidenceSig(kind,code)?stored.decision:'stale';
  }
  function reviewStamp(at){return at?String(at).replace('T',' ').replace(/\.\d+Z$/,' UTC').replace(/Z$/,' UTC'):'';}
  function reviewHistory(kind,code){
    const stored=reviews[rkey(kind,code)];
    const history=stored&&Array.isArray(stored.history)?stored.history:[];
    if(!history.length) return '';
    return `<details class="review-history" data-keep="hist-${kind}-${escapeHTML(code)}"><summary>Review history</summary><ul>${history.map(item=>`<li>${escapeHTML(item.decision)} · ${escapeHTML(reviewStamp(item.at))}</li>`).join('')}</ul></details>`;
  }
  function reviewNote(kind,code){
    const chip=reviewOf(kind,code)==='stale'?'<p class="stale-chip">Evidence changed since your review — review again</p>':'';
    return chip+reviewHistory(kind,code);
  }
  function reviewButtons(kind,code,label){
    const v=reviewOf(kind,code),c=escapeHTML(code);
    return `<div class="review" role="group" aria-label="Your review of ${escapeHTML(label)}"><button type="button" class="rv approve" data-review="${kind}" data-code="${c}" data-val="approve" aria-pressed="${v==='approve'}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>${kind==='notice'?'Approve to issue':'Approve'}</button><button type="button" class="rv hold" data-review="${kind}" data-code="${c}" data-val="hold" aria-pressed="${v==='hold'}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5.5 3.5v9M10.5 3.5v9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>Hold</button></div>`;
  }
  function reviewTally(plan){
    const items=[...plan.ranking.slice(0,budget).map(c=>['visit',c]),...plan.notices.map(n=>['notice',n.code])];
    const decided=decision=>decision==='approve'||decision==='hold';
    const done=items.filter(([k,c])=>decided(reviewOf(k,c))).length;
    return {total:items.length,done,approved:items.filter(([k,c])=>reviewOf(k,c)==='approve').length};
  }
  function setReview(kind,code,val){
    const k=rkey(kind,code), sig=evidenceSig(kind,code), prev=reviews[k];
    const same=prev&&typeof prev==='object'&&prev.decision===val&&prev.sig===sig;
    if(same) delete reviews[k];
    else{
      const history=Array.isArray(prev?.history)?prev.history.slice():[];
      if(prev&&typeof prev==='object'&&prev.decision&&prev.at) history.push({decision:prev.decision,sig:prev.sig,at:prev.at});
      reviews[k]={decision:val,sig,at:new Date().toISOString(),history:history.slice(-10)};
    }
    try{localStorage.setItem(REVIEW_KEY,JSON.stringify(reviews));}catch{}
    const open=[...document.querySelectorAll('details[open][data-keep]')].map(d=>d.dataset.keep);
    render();
    open.forEach(key=>document.querySelector(`details[data-keep="${CSS.escape(key)}"]`)?.setAttribute('open',''));
    document.querySelector(`[data-review="${kind}"][data-code="${CSS.escape(code)}"][data-val="${val}"]`)?.focus({preventScroll:true});
    const now=reviews[k];
    $('plan-status').textContent=`${code} ${kind}: ${!now?'review cleared':now.decision==='approve'?'approved':'on hold'}. Saved in this browser only.`;
  }
  function renderReview(plan){
    const t=reviewTally(plan),pct=t.total?Math.round(t.done/t.total*100):0;
    $('review-progress').hidden=!t.total;
    $('review-progress').innerHTML=`<div class="rp-top"><strong>${t.done} of ${t.total} reviewed</strong><span>${t.approved} approved · ${t.done-t.approved} on hold</span>${t.done?'<button type="button" class="rp-clear" data-clear-review>Clear my review</button>':''}</div><div class="rp-bar" role="progressbar" aria-label="Review progress" aria-valuemin="0" aria-valuemax="${t.total}" aria-valuenow="${t.done}"><i style="width:${pct}%"></i></div><p class="rp-note">Your choices are saved in this browser only. Nothing is sent anywhere.</p>`;
  }
  function reviewSlice(source,prefix){
    return Object.fromEntries(Object.entries(source).filter(([key])=>key.startsWith(prefix)));
  }
  function exportReview(){
    const prefix=`${cityId}|${mode}|`;
    const payload={app:'AfterStorm',format:1,exported_at:new Date().toISOString(),city:cityId,mode,
      reviews:reviewSlice(reviews,prefix),confirm:reviewSlice(confirmDates,prefix),citizen:reviewSlice(citizenAnswers,prefix)};
    const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json'}));
    const anchor=document.createElement('a');anchor.href=url;anchor.download=`afterstorm-review-${cityId}-${mode}.json`;
    document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('review-transfer-status').textContent=`Exported review file for ${data.cities[cityId].name} ${mode}. Keep it on your device or share it directly with your team.`;
  }
  function validReviewFile(payload){
    if(!payload||typeof payload!=='object'||Array.isArray(payload)||payload.app!=='AfterStorm'||payload.format!==1) throw Error('This is not an AfterStorm review file (format 1).');
    if(!Object.hasOwn(data.cities,payload.city)||!['live','replay'].includes(payload.mode)) throw Error('Review file has an unknown city or mode.');
    const prefix=`${payload.city}|${payload.mode}|`;
    const recordMap=(source,label,check)=>{
      if(!source||typeof source!=='object'||Array.isArray(source)) throw Error(`Review file has invalid ${label} records.`);
      const result=Object.create(null);
      for(const [key,value] of Object.entries(source)){
        if(!key.startsWith(prefix)||key.length>300||!value||typeof value!=='object'||Array.isArray(value)||!check(key,value)) throw Error(`Review file has an invalid ${label} entry.`);
        result[key]=value;
      }
      return result;
    };
    const str=(value,max=10000)=>typeof value==='string'&&value.length<=max;
    const isoDate=value=>str(value,10)&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value+'T00:00:00Z'));
    const reviewsIn=recordMap(payload.reviews,'review',(key,value)=>
      /^\w+\|(live|replay)\|(visit|notice)\|[A-Za-z0-9_-]+$/.test(key)&&['approve','hold'].includes(value.decision)&&str(value.sig)&&str(value.at,50)&&
      (!Object.hasOwn(value,'history')||(Array.isArray(value.history)&&value.history.length<=10&&value.history.every(h=>h&&typeof h==='object'&&!Array.isArray(h)&&['approve','hold'].includes(h.decision)&&str(h.sig)&&str(h.at,50)))));
    const confirmIn=recordMap(payload.confirm,'confirmation',(key,value)=>
      /^\w+\|(live|replay)\|[A-Za-z0-9_-]+$/.test(key)&&isoDate(value.date)&&str(value.sig));
    const allowed=new Set(['pipe','smell','faeces','sheen','contact','q6','q7','observed','photo']);
    const citizenIn=recordMap(payload.citizen,'citizen card',(key,value)=>
      /^\w+\|(live|replay)\|[A-Za-z0-9_-]+\|.+$/.test(key)&&Object.entries(value).every(([answer,entry])=>allowed.has(answer)&&str(entry,200)&&(['observed','photo'].includes(answer)||['yes','no','unsure'].includes(entry))));
    return {city:payload.city,mode:payload.mode,reviewsIn,confirmIn,citizenIn};
  }
  async function importReview(file){
    const status=$('review-transfer-status');
    if(!file) return;
    if(file.size>1024*1024){status.textContent='Review file rejected: the 1 MB limit was exceeded.';return;}
    if(!file.name.toLowerCase().endsWith('.json')){status.textContent='Review file rejected: choose a JSON file.';return;}
    try{
      const imported=validReviewFile(JSON.parse(await file.text()));
      Object.assign(reviews,imported.reviewsIn);Object.assign(confirmDates,imported.confirmIn);Object.assign(citizenAnswers,imported.citizenIn);
      localStorage.setItem(REVIEW_KEY,JSON.stringify(reviews));localStorage.setItem(CONFIRM_KEY,JSON.stringify(confirmDates));localStorage.setItem(CITIZEN_KEY,JSON.stringify(citizenAnswers));
      render();
      const counts=[Object.keys(imported.reviewsIn).length,Object.keys(imported.confirmIn).length,Object.keys(imported.citizenIn).length];
      const place=`${data.cities[imported.city].name} ${imported.mode}`;
      const message=`Imported ${counts[0]} decisions, ${counts[1]} confirmation dates and ${counts[2]} citizen cards for ${place}.`;
      $('plan-status').textContent=message;
      status.textContent=message;
      if(imported.city!==cityId||imported.mode!==mode){
        const button=document.createElement('button');button.type='button';button.textContent=`Switch to ${place}`;
        button.addEventListener('click',()=>{cityId=imported.city;mode=imported.mode;budget=Math.min(budget,data.cities[cityId].modes[mode].sites.length);render();status.textContent=message;});
        status.append(' ',button);
      }
    }catch(error){status.textContent=`Review file rejected: ${error.message}`;}
  }
  function downloadFhir(){
    const {city,plan}=view();
    const sites=new Map(plan.sites.map(site=>[site.code,site]));
    const selected=plan.ranking.slice(0,budget).map(code=>sites.get(code)).filter(site=>reviewOf('visit',site.code)!=='hold');
    if(!selected.length||selected.some(site=>!site?.service_request||!site.service_request_full_url)) return;
    const tags=[{system:'urn:afterstorm:export',code:'screen-slice',display:`mode=${mode}; budget=${budget}; city=${cityId}`}];
    if(data.fhir?.profile_tag) tags.push(data.fhir.profile_tag);
    const sentence=demonstrationSentence();
    if(sentence) tags.push({system:'urn:afterstorm:export',code:'demonstration',display:sentence});
    const bundle={resourceType:'Bundle',type:'transaction',meta:{tag:tags},entry:selected.map(site=>({fullUrl:site.service_request_full_url,resource:site.service_request,request:{method:'POST',url:'ServiceRequest'}}))};
    const url=URL.createObjectURL(new Blob([JSON.stringify(bundle,null,2)+'\n'],{type:'application/fhir+json'}));
    const link=document.createElement('a');
    link.href=url;link.download=`afterstorm-${cityId}-${mode}-budget-${budget}.json`;
    document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
    $('fhir-status').textContent=`Downloaded ${selected.length} draft ServiceRequest${selected.length===1?'':'s'} for ${city.name}, ${mode}, budget ${budget}. Nothing was sent.`;
  }
  const LAB_NOTE='Relative 2023–24 categories, not concentrations. Draft plan; nothing has been sent.';
  const LAB_COLUMNS=['rank','site_code','site_name','city','latitude','longitude','action','categories','stored_scores','window_start','window_end','window_label','review','draft_notice','confirmation_sample_date','sewage_distance_m','filed_service_request','note'];
  function csvField(value){return `"${String(value??'').replaceAll('"','""')}"`;}
  function storedScores(site){
    const health=site.source_health;
    if(!health) return 'no public lab result';
    const fields={faecal:'scaledFecalRisk',pathogen:'scaledPathogenRisk','antibiotic resistance':'scaledArgRisk'};
    const parts=(site.categories||[]).map(label=>{const value=health[fields[label]];return numeric(value)?`${label} ${Number(value).toFixed(2)}`:null;}).filter(Boolean);
    return parts.length?parts.join('; '):'no public lab result';
  }
  function labAction(site){
    if(site.action==='new category assessment') return 'post-storm reassessment';
    if(site.action==='first baseline assessment') return 'first baseline assessment';
    return site.action||'';
  }
  function labReview(code){
    const state=reviewOf('visit',code);
    return state==='approve'?'approved':state==='hold'?'on hold':state==='stale'?'evidence changed':'not reviewed';
  }
  function filedCell(code){
    if(!filedMatches()) return '';
    const item=filed.resources.find(row=>row.code===code&&row.id);
    return item?`ServiceRequest/${item.id} (shape v1)`:'';
  }
  function labSheetRows(){
    const {city,plan}=view();
    const sites=new Map(plan.sites.map(site=>[site.code,site]));
    const rows=[LAB_COLUMNS];
    plan.ranking.slice(0,budget).forEach(code=>{
      const site=sites.get(code); if(!site) return;
      const pos=site.position||{};
      const record=confirmRecord(code);
      rows.push([
        site.rank??'', site.code, site.name||'', city.name,
        numeric(pos.latitude)?String(pos.latitude):'', numeric(pos.longitude)?String(pos.longitude):'',
        labAction(site), (site.categories||[]).join('; '), storedScores(site),
        site.window?.start_date||'', site.window?.end_date||'', site.window?'experimental, heuristic, not validated':'',
        labReview(code), site.draft_notice?'yes':'no',
        record&&record.kind==='set'?record.date:'',
        numeric(site.sewage_distance_m)?String(site.sewage_distance_m):'',
        filedCell(code), LAB_NOTE
      ]);
    });
    return rows;
  }
  function labSheetCsv(){return `\uFEFF${labSheetRows().map(row=>row.map(csvField).join(',')).join('\r\n')}\r\n`;}
  function downloadLabSheet(){
    const {city}=view();
    const url=URL.createObjectURL(new Blob([labSheetCsv()],{type:'text/csv;charset=utf-8'}));
    const link=document.createElement('a');
    link.href=url;link.download=`afterstorm-${cityId}-${mode}-lab-sheet.csv`;
    document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
    $('fhir-status').textContent=`Downloaded the lab sheet for ${city.name}, ${mode}, budget ${budget}. Nothing was sent.`;
  }
  function groupedMetres(value){
    const rounded=Math.round(value), text=String(Math.abs(rounded)).replace(/\B(?=(\d{3})+(?!\d))/g,',');
    return `${rounded<0?'-':''}${text} m`;
  }
  function settingRows(site){
    const setting=site?.urban_setting||{};
    const hospital=numeric(setting.distanceToHospitals)?setting.distanceToHospitals:null;
    const impervious=numeric(setting.imperviousPct100m)?setting.imperviousPct100m:null;
    const veg=numeric(setting.vegCoverFrac100m)?setting.vegCoverFrac100m:null;
    const density=numeric(setting.humanDensityProxy100m)?setting.humanDensityProxy100m:null;
    const raw=value=>value===null?'Missing':String(value);
    return {
      compact:`Nearest hospital ${hospital===null?'Missing':groupedMetres(hospital)} · impervious surface within 100 m ${impervious===null?'Missing':raw(impervious)+' %'} · vegCoverFrac100m ${raw(veg)} · humanDensityProxy100m ${density===null?'Missing':raw(density)+' — a relative proxy, not a head count'}`,
      rows:[
        `Nearest hospital: ${hospital===null?'Missing':groupedMetres(hospital)} (distanceToHospitals)`,
        `Impervious surface within 100 m: ${impervious===null?'Missing':raw(impervious)+' %'} (imperviousPct100m)`,
        `vegCoverFrac100m: ${raw(veg)}`,
        `humanDensityProxy100m: ${density===null?'Missing':raw(density)+' — a relative proxy, not a head count'}`
      ]
    };
  }
  const CONFIRM_KEY='afterstorm-confirm-v2';
  const CONFIRM_DIRECTIVE='Directive 2006/7/EC Annex IV.4: In the event of short-term pollution, one additional sample is to be taken to confirm that the incident has ended. This sample is not to be part of the set of bathing water quality data.';
  const LA_SENTENCE="For comparison, Los Angeles County advises avoiding ocean water for 72 hours after rain ends. That advisory is not this prototype's 20 mm setting or its two-day window.";
  const DIRECTIVE_LEAD='Under the EU Bathing Water Directive, one extra sample confirms that a short-term pollution incident has ended; the coordinator sets that date here.';
  let confirmDates={};try{confirmDates=JSON.parse(localStorage.getItem(CONFIRM_KEY))||{};}catch{confirmDates={};}
  function nextIso(iso){
    const [year,month,day]=iso.split('-').map(Number);
    const date=new Date(Date.UTC(year,month-1,day));
    date.setUTCDate(date.getUTCDate()+1);
    return date.toISOString().slice(0,10);
  }
  function confirmationMin(site){
    const end=site.window?.end_date||view().plan.storm?.window?.end_date;
    if(end) return nextIso(end);
    const period=view().plan.forecast_period||data.cities[cityId].modes.live.forecast_period;
    return period?.start_date||'';
  }
  function confirmRecord(code){
    const stored=confirmDates[`${cityId}|${mode}|${code}`];
    if(!stored||typeof stored!=='object'||!/^\d{4}-\d{2}-\d{2}$/.test(stored.date||'')) return null;
    return stored.sig===evidenceSig('notice',code)?{kind:'set',date:stored.date}:{kind:'stale'};
  }
  function confirmStatus(code){
    const record=confirmRecord(code);
    if(!record) return '<p class="confirm-status">No confirmation date set yet</p>';
    if(record.kind==='stale') return '<p class="stale-chip">Evidence changed — set the confirmation date again</p>';
    return `<p class="confirm-status">Confirmation sample planned for ${escapeHTML(fullDate(record.date))}</p>`;
  }
  function saveConfirmDate(input){
    const code=input.dataset.confirmDate;
    const key=`${cityId}|${mode}|${code}`;
    if(input.min&&input.value&&input.value<input.min) input.value='';
    if(/^\d{4}-\d{2}-\d{2}$/.test(input.value)) confirmDates[key]={date:input.value,sig:evidenceSig('notice',code)};
    else delete confirmDates[key];
    try{localStorage.setItem(CONFIRM_KEY,JSON.stringify(confirmDates));}catch{}
    const strip=input.closest('.confirm-strip');
    const current=strip?.querySelector('.confirm-status, .stale-chip');
    if(!current) return;
    const holder=document.createElement('div');
    holder.innerHTML=confirmStatus(code);
    current.replaceWith(holder.firstElementChild);
  }
  function confirmStrip(site){
    if(!site?.confirmation_sample) return '';
    const record=confirmRecord(site.code);
    const value=record&&record.kind==='set'?` value="${record.date}"`:'';
    const min=confirmationMin(site);
    return `<div class="confirm-strip">${confirmStatus(site.code)}<label class="field">Confirmation sample date<input type="date" data-confirm-date="${escapeHTML(site.code)}"${min?` min="${min}"`:''}${value}></label></div>`;
  }
  function confirmationBlock(site){
    const sample=site?.confirmation_sample;
    if(!sample) return '';
    return `<div class="setting-block confirm-sample"><p><strong>Confirmation sample</strong></p><p>${escapeHTML(sample.purpose)}</p><p>${escapeHTML(sample.not_a_class)}</p><p class="setting-note">${escapeHTML(sample.date_note)}</p><p class="setting-note">${escapeHTML(CONFIRM_DIRECTIVE)}</p></div>`;
  }
  function renderNotices(plan){
    $('notice-count').textContent=String(plan.notices.length);
    if(!plan.notices.length){
      const explanation=plan.storm?'No valid faecal or pathogen category reaches the notice threshold in this city. An antibiotic-resistance assessment alone does not trigger a contact notice.':'No storm scenario is selected, so no contact notices are drafted.';
      $('notices').innerHTML=`<p class="notice-description">${escapeHTML(explanation)}</p><p class="notice-description">${escapeHTML(LA_SENTENCE)}</p>`;
      return;
    }
    const noticeRows=plan.notices.map(notice=>{
      const site=plan.sites.find(s=>s.code===notice.code);
      const v=reviewOf('notice',notice.code);
      const setting=settingRows(site);
      return `<div class="notice-row rv-${v||'none'}" data-code="${escapeHTML(notice.code)}"><div class="notice-head"><code>${escapeHTML(notice.code)}</code><span class="notice-name">${escapeHTML(site?.name||notice.code)}<span class="notice-state">${v==='approve'?'Approved to issue · not sent':v==='hold'?'On hold':'Draft — needs review'}</span></span>${reviewButtons('notice',notice.code,'notice for '+notice.code)}</div>${confirmStrip(site)}<p class="setting-line">${escapeHTML(setting.compact)}</p>${reviewNote('notice',notice.code)}<details class="notice-more" data-keep="notice-${escapeHTML(notice.code)}"><summary>Read the draft notice</summary><p class="notice-tag" style="margin-top:10px">${escapeHTML(notice.label)}</p><p class="notice-text">${escapeHTML(notice.text)}</p><p class="notice-basis">${escapeHTML(notice.basis)}</p><p class="notice-basis">${escapeHTML(notice.review)}</p><div class="setting-block"><p><strong>Setting around this stream</strong> (stored values from the Resilience Map urban parameters)</p><ul>${setting.rows.map(line=>`<li>${escapeHTML(line)}</li>`).join('')}</ul><p class="setting-note">These values describe the surroundings. They don't change the visit order or the notice.</p></div>${confirmationBlock(site)}</details></div>`;
    }).join('');
    $('notices').innerHTML=`<p class="notice-description">Draft — requires coordinator review. You decide whether to issue each notice and when to lift it. Approving here only records your decision; nothing is sent. ${escapeHTML(DIRECTIVE_LEAD)}</p>`+noticeRows+`<p class="notice-description">${escapeHTML(LA_SENTENCE)}</p>`;
  }
  function renderRoster(plan,allocated){
    $('roster-heading').textContent=`All ${plan.sites.length} sites and planning status`;
    $('all-sites').innerHTML=plan.sites.map(site=>{const status=planningStatus(site,allocated);return `<tr data-code="${escapeHTML(site.code)}"><td><code>${escapeHTML(site.code)}</code></td><td>${escapeHTML(site.name)}${site.map_note?`<small>${escapeHTML(site.map_note)}</small>`:''}</td><td><span class="badge ${status.kind==='baseline'?'blue':status.kind==='capacity'?'replay':status.kind==='sample'?'':'grey'}">${escapeHTML(status.label)}</span></td><td class="table-reason">${escapeHTML(site.reason)}</td><td>${site.position?`<button type="button" class="locate" data-locate="${escapeHTML(site.code)}" aria-label="Show ${escapeHTML(site.code)} on map">Show on map</button>`:'No coordinates'}</td></tr>`;}).join('');
    $('excluded-heading').textContent=`Excluded and why · ${plan.excluded.length}`;
    $('excluded-body').innerHTML=plan.excluded.length?plan.excluded.map(s=>`<p><code>${escapeHTML(s.code)}</code> ${escapeHTML(s.reason)}</p>`).join(''):'<p>No sites are excluded for invalid lab source data in this city/mode. Sites without lab results remain baseline candidates.</p>';
  }
  function renderCoverage(plan){
    const archive=data.cities[cityId].modes.replay.archive;
    if(!archive){$('coverage').hidden=true;return;}
    $('coverage').hidden=false;
    const observed=archive.valid_dates.length,heavy=archive.heavy_rain_days,rate=observed?((heavy/observed)*365.25).toFixed(1):null;
    $('coverage').innerHTML=`<summary>How often do storms like this hit ${escapeHTML(data.cities[cityId].name)}?</summary><p>${rate?`About <strong class="mono">${rate}</strong> days a year bring ${data.config.RAIN_MM} mm or more to every site at once.`:'Not enough rain data to say.'}</p><p>Based on <span class="mono">${observed}</span> days with rain data at every site, <span class="mono">${heavy}</span> of which qualified. <span class="mono">${archive.unknown_dates.length}</span> days lack data at one or more sites (this includes days before some sites' records begin). This describes the past, not future rain.</p>`;
  }
  function mapStatus(){
    $('map-status').textContent=!$('basemap').checked?'Street map off. Pins use saved coordinates; map tiles need internet.':tileFailed?'Street map unavailable. Pins remain on a plain background. Map tiles need internet.':'Map tiles need internet. Pins and the plan use saved data.';
  }
  function initializeMap(){
    if(!window.L) throw new Error('The local map library is unavailable. Check that web/vendor/leaflet.js is present.');
    leafletMap=L.map('map',{scrollWheelZoom:false,zoomControl:true,zoomSnap:.25,wheelPxPerZoomLevel:45});
    markerGroup=L.layerGroup().addTo(leafletMap);
    // Pinch (ctrl+wheel) always zooms; plain scroll zooms only after the map is clicked, so the page never gets trapped.
    const frame=$('map').parentElement,hint=$('map-hint');let active=false,hintTimer;
    const activate=on=>{active=on;frame.classList.toggle('map-active',on);on?leafletMap.scrollWheelZoom.enable():leafletMap.scrollWheelZoom.disable();};
    frame.addEventListener('wheel',event=>{
      if(event.ctrlKey||event.metaKey||active){leafletMap.scrollWheelZoom.enable();return;}
      leafletMap.scrollWheelZoom.disable();hint.classList.add('show');clearTimeout(hintTimer);hintTimer=setTimeout(()=>hint.classList.remove('show'),1400);
    },{capture:true,passive:true});
    leafletMap.on('click focus',()=>activate(true));
    frame.addEventListener('mouseleave',()=>activate(false));
    leafletMap.on('blur',()=>activate(false));
    tileLayer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'});
    tileLayer.on('tileerror',()=>{tileFailed=true;mapStatus();});
    tileLayer.addTo(leafletMap);
    $('basemap').addEventListener('change',()=>{if($('basemap').checked){tileFailed=false;tileLayer.addTo(leafletMap);}else leafletMap.removeLayer(tileLayer);mapStatus();});
  }
  function renderMap(city,plan,allocated){
    markerGroup.clearLayers();markers.clear();pins.clear();
    const positioned=plan.sites.filter(s=>s.position&&numeric(s.position.latitude)&&numeric(s.position.longitude));
    $('map-heading').textContent=`Streams in ${city.name}`;
    $('map-count').textContent=`${plan.sites.length} sites · ${positioned.length} with coordinates`;
    // Unplanned sites first, so numbered pins always draw on top.
    positioned.sort((x,y)=>allocated.has(x.code)-allocated.has(y.code));
    for(const site of positioned){
      const status=planningStatus(site,allocated),active=allocated.has(site.code),ll=[site.position.latitude,site.position.longitude];
      const popup=document.createElement('div');
      popup.innerHTML=`<strong><code>${escapeHTML(site.code)}</code> · ${escapeHTML(site.name)}</strong><br>${escapeHTML(status.label)}${site.categories.length?'<br>'+escapeHTML(site.categories.join(' + ')):''}${site.draft_notice?'<br><span class="notice-tag">Draft notice — needs review</span>':''}`;
      let marker;
      if(active){
        const rv=reviewOf('visit',site.code),held=rv==='hold';
        marker=L.marker(ll,{keyboard:true,title:`Visit ${site.rank}: ${site.code} ${site.name}`,riseOnHover:true,zIndexOffset:1000-site.rank,
          icon:L.divIcon({className:'pin-wrap',iconSize:[26,26],iconAnchor:[13,30],popupAnchor:[0,-28],html:`<div class="pin${site.draft_notice?' notice':''}${held?' held':''}${rv==='approve'?' ok':''}" style="--c:${status.color}"><span>${site.rank}</span></div>`})});
        marker.on('click',()=>{focusCard(site.code);});
        marker.on('mouseover',()=>highlight(site.code));marker.on('mouseout',()=>highlight(null));
        pins.set(site.code,marker);
      }else{
        marker=L.circleMarker(ll,{radius:5.5,color:site.draft_notice?'#976124':status.color,weight:site.draft_notice?3:1.5,fillColor:status.color,fillOpacity:.6});
        marker.bindPopup(popup);
      }
      marker.addTo(markerGroup);markers.set(site.code,marker);
      if(active) marker.bindPopup(popup);
    }
    const mapKey=`${cityId}|${mode}`;if(previousMapCity!==mapKey){
      const focus=positioned.filter(s=>allocated.has(s.code));const frame=focus.length>=2?focus:positioned;
      if(frame.length) leafletMap.fitBounds(L.latLngBounds(frame.map(s=>[s.position.latitude,s.position.longitude])),{padding:[45,45],maxZoom:14});
      else leafletMap.setView([city.latitude,city.longitude],12);
      previousMapCity=mapKey;
    }
    mapStatus();
  }
  function highlight(code){
    document.querySelectorAll('.visit-card.hl').forEach(c=>c.classList.remove('hl'));
    pins.forEach(m=>m.getElement()?.querySelector('.pin')?.classList.remove('hl'));
    if(!code) return;
    $(`visit-${code}`)?.classList.add('hl');
    pins.get(code)?.getElement()?.querySelector('.pin')?.classList.add('hl');
  }
  function focusCard(code){
    const card=$(`visit-${code}`); if(!card) return;
    highlight(code);
    const r=card.getBoundingClientRect();
    if(r.top<0||r.bottom>innerHeight) card.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});
    card.classList.remove('flash');void card.offsetWidth;card.classList.add('flash');
  }
  const CITIZEN_KEY='afterstorm-citizen-v1';
  const CARD_I18N = {
    "en": {
      "titleStorm": "After-storm look — citizen task card",
      "titleFirst": "First look — citizen task card",
      "safety": "Stay on the bank or path. Do not enter or touch the water. Do not collect water samples — the lab team does that. Wash your hands afterwards.",
      "q1": "A pipe or outfall is discharging into the stream",
      "q2": "Sewage smell",
      "q3": "Animal faeces on the bank or path",
      "q4": "Foam, scum or oily sheen on the water",
      "q5": "People or pets in the water",
      "ecoHeading": "Animal and ecosystem signs",
      "q6": "Dead fish or other dead animals in or near the water",
      "q7": "Unusual water colour or a green algae bloom",
      "yes": "Yes",
      "no": "No",
      "unsure": "Unsure",
      "observed": "Observed on (date and time)",
      "photo": "Photo reference (e.g., your OneAquaHealth app record)"
    },
    "pt": {
      "titleStorm": "Observação pós-tempestade — ficha de tarefa cidadã",
      "titleFirst": "Primeira observação — ficha de tarefa cidadã",
      "safety": "Fique na margem ou no caminho. Não entre na água nem lhe toque. Não recolha amostras de água — essa tarefa é da equipa do laboratório. Lave as mãos no fim.",
      "q1": "Há um cano ou descarga a despejar no ribeiro",
      "q2": "Cheiro a esgoto",
      "q3": "Fezes de animais na margem ou no caminho",
      "q4": "Espuma, escuma ou película oleosa na água",
      "q5": "Pessoas ou animais de estimação na água",
      "ecoHeading": "Sinais nos animais e no ecossistema",
      "q6": "Peixes ou outros animais mortos na água ou perto dela",
      "q7": "Cor da água invulgar ou proliferação de algas verdes",
      "yes": "Sim",
      "no": "Não",
      "unsure": "Não tenho a certeza",
      "observed": "Observado em (data e hora)",
      "photo": "Referência da fotografia (p. ex., o seu registo na app OneAquaHealth)"
    },
    "fr": {
      "titleStorm": "Observation après l'orage — fiche de mission citoyenne",
      "titleFirst": "Premier regard — fiche de mission citoyenne",
      "safety": "Restez sur la berge ou le chemin. N'entrez pas dans l'eau et ne la touchez pas. Ne prélevez pas d'échantillons d'eau — l'équipe du laboratoire s'en charge. Lavez-vous les mains ensuite.",
      "q1": "Un tuyau ou une sortie d'eau se déverse dans le cours d'eau",
      "q2": "Odeur d'égout",
      "q3": "Excréments d'animaux sur la berge ou le chemin",
      "q4": "Mousse, écume ou film huileux sur l'eau",
      "q5": "Des personnes ou des animaux de compagnie dans l'eau",
      "ecoHeading": "Signes chez les animaux et dans l'écosystème",
      "q6": "Poissons ou autres animaux morts dans l'eau ou à proximité",
      "q7": "Couleur de l'eau inhabituelle ou prolifération d'algues vertes",
      "yes": "Oui",
      "no": "Non",
      "unsure": "Je ne sais pas",
      "observed": "Observé le (date et heure)",
      "photo": "Référence de la photo (p. ex. votre relevé dans l'appli OneAquaHealth)"
    },
    "nl": {
      "titleStorm": "Kijk na de storm — burgertaakkaart",
      "titleFirst": "Eerste kijk — burgertaakkaart",
      "safety": "Blijf op de oever of het pad. Ga niet in het water en raak het niet aan. Neem geen waterstalen — dat doet het labteam. Was daarna je handen.",
      "q1": "Een buis of uitlaat loost in de beek",
      "q2": "Rioolgeur",
      "q3": "Dierenuitwerpselen op de oever of het pad",
      "q4": "Schuim of een olieachtige laag op het water",
      "q5": "Mensen of huisdieren in het water",
      "ecoHeading": "Signalen bij dieren en in het ecosysteem",
      "q6": "Dode vissen of andere dode dieren in of bij het water",
      "q7": "Ongewone waterkleur of groene algenbloei",
      "yes": "Ja",
      "no": "Nee",
      "unsure": "Weet niet",
      "observed": "Waargenomen op (datum en tijd)",
      "photo": "Fotoreferentie (bv. je registratie in de OneAquaHealth-app)"
    },
    "it": {
      "titleStorm": "Osservazione dopo il temporale — scheda attività per cittadini",
      "titleFirst": "Primo sguardo — scheda attività per cittadini",
      "safety": "Resta sulla sponda o sul sentiero. Non entrare in acqua e non toccarla. Non prelevare campioni d'acqua: se ne occupa il laboratorio. Lavati le mani al termine.",
      "q1": "Un tubo o uno scarico sta riversando nel corso d'acqua",
      "q2": "Odore di fogna",
      "q3": "Feci di animali sulla sponda o sul sentiero",
      "q4": "Schiuma o pellicola oleosa sull'acqua",
      "q5": "Persone o animali domestici in acqua",
      "ecoHeading": "Segnali su animali ed ecosistema",
      "q6": "Pesci o altri animali morti nell'acqua o vicino",
      "q7": "Colore dell'acqua insolito o fioritura di alghe verdi",
      "yes": "Sì",
      "no": "No",
      "unsure": "Non so",
      "observed": "Osservato il (data e ora)",
      "photo": "Riferimento foto (ad es. la tua registrazione nell'app OneAquaHealth)"
    },
    "nb": {
      "titleStorm": "Etter uværet — oppgavekort for innbyggere",
      "titleFirst": "Første titt — oppgavekort for innbyggere",
      "safety": "Hold deg på bredden eller stien. Ikke gå uti eller ta på vannet. Ikke ta vannprøver – det gjør laboratorieteamet. Vask hendene etterpå.",
      "q1": "Et rør eller utløp slipper ut i bekken",
      "q2": "Kloakklukt",
      "q3": "Dyremøkk på bredden eller stien",
      "q4": "Skum eller oljeaktig hinne på vannet",
      "q5": "Mennesker eller kjæledyr i vannet",
      "ecoHeading": "Tegn hos dyr og i økosystemet",
      "q6": "Døde fisker eller andre døde dyr i eller ved vannet",
      "q7": "Uvanlig vannfarge eller grønn algeoppblomstring",
      "yes": "Ja",
      "no": "Nei",
      "unsure": "Usikker",
      "observed": "Observert (dato og klokkeslett)",
      "photo": "Bildereferanse (f.eks. registreringen din i OneAquaHealth-appen)"
    }
  };
  const CITY_LANG = {CO:'pt', TO:'fr', GH:'nl', BE:'it', OS:'nb'};
  const cardLangChoice = {};
  const CITIZEN_QUESTIONS = ['pipe', 'smell', 'faeces', 'sheen', 'contact', 'q6', 'q7'];
  let citizenAnswers={};try{citizenAnswers=JSON.parse(localStorage.getItem(CITIZEN_KEY))||{};}catch{citizenAnswers={};}
  function citizenStoreKey(code){return `${cityId}|${mode}|${code}|${evidenceSig('visit',code)}`;}
  function cardPack(){
    const lang=cardLangChoice[cityId]||CITY_LANG[cityId]||'en';
    return {lang, text:CARD_I18N[lang]||CARD_I18N.en};
  }
  function citizenTitle(site, text){
    text=text||cardPack().text;
    return site.action==='first baseline assessment'?text.titleFirst:text.titleStorm;
  }
  function choiceLabel(text, value){
    if(value==='yes') return text.yes;
    if(value==='no') return text.no;
    if(value==='unsure') return text.unsure;
    return 'not answered';
  }
  function citizenWhen(site){return site.window?`${dateRange(site.window)} (experimental window)`:'any day';}
  function citizenWhere(site){const pos=site.position;return pos&&numeric(pos.latitude)&&numeric(pos.longitude)?`${Number(pos.latitude).toFixed(5)}, ${Number(pos.longitude).toFixed(5)}`:'No coordinates';}
  function readCitizenCard(card){
    const answers={};
    card.querySelectorAll('input[type=radio]:checked').forEach(input=>{answers[input.dataset.q]=input.value;});
    card.querySelectorAll('[data-q-text]').forEach(input=>{answers[input.dataset.qText]=input.value;});
    return answers;
  }
  function saveCitizenCard(card){
    citizenAnswers[citizenStoreKey(card.dataset.code)]=readCitizenCard(card);
    try{localStorage.setItem(CITIZEN_KEY,JSON.stringify(citizenAnswers));}catch{}
  }
  function answersFor(code){
    const card=document.querySelector(`.task-card[data-code="${CSS.escape(code)}"]`);
    return card?readCitizenCard(card):(citizenAnswers[citizenStoreKey(code)]||{});
  }
  function citizenCard(site){
    const saved=citizenAnswers[citizenStoreKey(site.code)]||{};
    const pack=cardPack(), text=pack.text, english=pack.lang==='en';
    const fields=CITIZEN_QUESTIONS.map((id,index)=>`${index===5?`<h4 class="eco-heading">${escapeHTML(text.ecoHeading)}</h4>`:''}<fieldset><legend>${escapeHTML(text['q'+(index+1)])}</legend>${[['yes',text.yes],['no',text.no],['unsure',text.unsure]].map(([value,label])=>`<label class="task-choice"><input type="radio" name="task-${escapeHTML(site.code)}-${id}" data-q="${id}" value="${value}"${saved[id]===value?' checked':''}> ${escapeHTML(label)}</label>`).join('')}</fieldset>`).join('');
    const draft=english?'':`<p class="translation-draft" lang="en">Translation draft — have a native speaker check it before field use.</p>`;
    return `<details class="task-card" lang="${pack.lang}" data-code="${escapeHTML(site.code)}"><summary lang="en">Task card</summary><div class="sheet-panel" role="dialog" aria-label="Citizen task card for ${escapeHTML(site.code)}"><div class="sheet-head" lang="en"><span>Citizen task card · <strong>${escapeHTML(site.code)}</strong></span><button type="button" class="sheet-close" data-close-sheet aria-label="Close">×</button></div><div class="lang-switch" role="group" aria-label="Card language" lang="en"><button type="button" data-card-lang="city" aria-pressed="${!english}">City language</button><button type="button" data-card-lang="en" aria-pressed="${english}">English</button></div><div class="task-body"><h3>${escapeHTML(citizenTitle(site,text))}</h3><p><strong>${escapeHTML(site.code)}</strong> ${escapeHTML(site.name)}</p><p>${escapeHTML(citizenWhere(site))}</p><p>${escapeHTML(citizenWhen(site))}</p><p class="task-safety">${escapeHTML(text.safety)}</p>${fields}<p lang="en">Report dead fish or animals to the city or environmental authority as well. These observations don't change the visit order, the tests or any notice.</p><label class="field">${escapeHTML(text.observed)}<input type="text" data-q-text="observed" value="${escapeHTML(saved.observed||'')}"></label><label class="field">${escapeHTML(text.photo)}<input type="text" data-q-text="photo" value="${escapeHTML(saved.photo||'')}"></label>${draft}<p lang="en">Saved in this browser only. Nothing is sent.</p><p class="task-links" lang="en"><a href="https://apps.oneaquahealth.eu/" target="_blank" rel="noopener">Open the OneAquaHealth Citizen Science App</a> · <a href="https://www.oneaquahealth.eu/citizen-science-project/" target="_blank" rel="noopener">How to install it</a></p><p lang="en">These observations give the coordinator context. They don't change the visit order, the tests, or any notice. Record the full stream assessment in the official OneAquaHealth Citizen Science App (a login is required); this card only adds the after-storm checks.</p><button type="button" class="print-one" lang="en" data-print-card="${escapeHTML(site.code)}">Print this card</button></div></div></details>`;
  }
  function citizenPrintArticle(site,answers){
    const pack=cardPack(), text=pack.text;
    const questions=CITIZEN_QUESTIONS.map((id,index)=>`${index===5?`<h3>${escapeHTML(text.ecoHeading)}</h3>`:''}<p><strong>${escapeHTML(text['q'+(index+1)])}:</strong> ${escapeHTML(choiceLabel(text, answers[id]))}</p>`).join('');
    const draft=pack.lang==='en'?'':`<p lang="en">Translation draft — have a native speaker check it before field use.</p>`;
    return `<article class="task-sheet" lang="${pack.lang}"><h2>${escapeHTML(citizenTitle(site,text))}</h2><p><strong>${escapeHTML(site.code)}</strong> ${escapeHTML(site.name)}</p><p>${escapeHTML(citizenWhere(site))}</p><p>${escapeHTML(citizenWhen(site))}</p><p><strong>${escapeHTML(text.safety)}</strong></p>${questions}<p>${escapeHTML(text.observed)}: ${escapeHTML(answers.observed||'')}</p><p>${escapeHTML(text.photo)}: ${escapeHTML(answers.photo||'')}</p>${draft}<p lang="en" class="task-links"><a href="https://apps.oneaquahealth.eu/" target="_blank" rel="noopener">Open the OneAquaHealth Citizen Science App</a> · <a href="https://www.oneaquahealth.eu/citizen-science-project/" target="_blank" rel="noopener">How to install it</a></p><p lang="en">These observations give the coordinator context. They don't change the visit order, the tests, or any notice. Record the full stream assessment in the official OneAquaHealth Citizen Science App (a login is required); this card only adds the after-storm checks.</p><p lang="en">Saved in this browser only. Nothing is sent.</p></article>`;
  }
  function printTaskCards(codes){
    const sites=new Map(view().plan.sites.map(site=>[site.code,site]));
    $('print-area').innerHTML=codes.filter(code=>sites.has(code)).map(code=>citizenPrintArticle(sites.get(code),answersFor(code))).join('');
    document.body.classList.add('print-card');
    const cleanup=()=>{document.body.classList.remove('print-card');$('print-area').innerHTML='';window.removeEventListener('afterprint',cleanup);};
    window.addEventListener('afterprint',cleanup);
    window.print();
  }
  function categoryList(labels){
    if(labels.length<2) return labels[0]||'';
    if(labels.length===2) return `${labels[0]} and ${labels[1]}`;
    return `${labels.slice(0,-1).join(', ')} and ${labels.at(-1)}`;
  }
  function renderProtection(plan,allocated){
    const sites=new Map(plan.sites.map(site=>[site.code,site]));
    const picked=plan.ranking.slice(0,budget).map(code=>sites.get(code)).filter(Boolean);
    const noNoticeVisits=picked.filter(site=>!site.draft_notice);
    const noticeOutside=plan.sites.filter(site=>site.draft_notice&&!allocated.has(site.code)).sort((a,b)=>(a.rank??1e9)-(b.rank??1e9));
    const rankedNotices=plan.sites.filter(site=>site.draft_notice&&Number.isInteger(site.rank));
    const budgetForAllNotices=rankedNotices.length?Math.max(...rankedNotices.map(site=>site.rank)):null;
    const line=data.config.ADVISORY_MIN;
    const two=value=>Number(value).toFixed(2);
    const nearLine=plan.sites.filter(site=>{
      const health=site.source_health;
      if(!health||site.draft_notice) return false;
      const highest=Math.max(numeric(health.scaledFecalRisk)?health.scaledFecalRisk:-1,numeric(health.scaledPathogenRisk)?health.scaledPathogenRisk:-1);
      return highest>=0.45&&highest<line;
    }).sort((a,b)=>(a.rank??1e9)-(b.rank??1e9));
    const section=$('protection');
    if(!plan.notices.length&&!nearLine.length){section.hidden=true;$('protection-body').innerHTML='';return;}
    section.hidden=false;
    const contactPhrase=site=>{
      const health=site.source_health||{};
      const pairs=[['faecal',health.scaledFecalRisk],['pathogen',health.scaledPathogenRisk]].filter(([,value])=>numeric(value));
      if(!pairs.length) return 'faecal or pathogen value missing';
      const top=Math.max(...pairs.map(([,value])=>value));
      return pairs.filter(([,value])=>value===top).map(([label,value])=>`${label} ${two(value)}`).join(' and ');
    };
    const nearPhrase=site=>{
      const health=site.source_health;
      return [['faecal',health.scaledFecalRisk],['pathogen',health.scaledPathogenRisk]].filter(([,value])=>numeric(value)&&value>=0.45).map(([label,value])=>`${label} ${two(value)}`).join(', ');
    };
    const parts=[];
    if(!plan.storm) parts.push(`<p>No storm in this view, so no contact notices are drafted.</p>`);
    noticeOutside.forEach(site=>{
      const metres=numeric(site.sewage_distance_m)?`${Math.round(site.sewage_distance_m)} m`:'distance missing';
      parts.push(`<p><strong>${escapeHTML(site.code)} ${escapeHTML(site.name)}</strong> has a draft contact notice (${escapeHTML(contactPhrase(site))} · sewage works ${escapeHTML(metres)}) but sits outside the ${budget}-visit budget. Only a new sample there can confirm or lift its notice.</p>`);
    });
    // Group no-notice visits by their categories so five identical lines read as one sentence.
    const groups=new Map();
    noNoticeVisits.forEach(site=>{const key=categoryList(site.categories);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(site);});
    groups.forEach((list,cats)=>{
      if(list.length===1){const site=list[0];parts.push(`<p>Visit ${site.rank}, <strong>${escapeHTML(site.code)}</strong>, reassesses ${escapeHTML(cats)} and drafts no contact notice.</p>`);return;}
      const all=list.length===picked.length;
      parts.push(`<p>${all?`All ${list.length} planned visits`:`Visits ${list.map(s=>s.rank).join(', ')}`} (${list.map(s=>`<strong>${escapeHTML(s.code)}</strong>`).join(', ')}) reassess ${escapeHTML(cats)} and draft no contact notice.</p>`);
    });
    if(noticeOutside.length&&noNoticeVisits.length&&budgetForAllNotices!==null){
      parts.push(`<p><button type="button" class="cover-notices" data-cover-notices="${budgetForAllNotices}">Show a budget that covers every notice site (${budgetForAllNotices} visits)</button></p>`);
    }
    if(nearLine.length){
      parts.push(`<p>${plan.storm?'Just under':'Closest to'} the prototype notice setting (${escapeHTML(String(line))}): ${nearLine.map(site=>`<strong>${escapeHTML(site.code)}</strong> ${escapeHTML(nearPhrase(site))}`).join('; ')}.</p>`);
    }
    if(plan.notices.length&&!noticeOutside.length) parts.push('<p>Every site with a draft notice is in this plan.</p>');
    parts.push('<p class="protection-foot">The plan ranks visits by the highest stored category. This check shows what that order leaves out for people-and-pets protection. It does not change the order or the filed requests.</p>');
    $('protection-body').innerHTML=parts.join('');
  }
  function renderSources(){
    const refs=[['sites.json','Official site roster'],['health-risks.json','Lab category results'],['urban-parameters.json','Urban parameters'],[`forecasts/${cityId}.json`,'City forecast']];
    $('source-summary').innerHTML=refs.map(([name,label])=>{const s=data.sources[name]||{};return `<p>${link(s.url,label)} · fetched <span class="mono">${escapeHTML(timestamp(s.fetched_at))}</span></p>`;}).join('')+`<p><strong>Prototype settings, not validated environmental rules:</strong> a storm is ${data.config.RAIN_MM} mm of rain or more in a day. A test is proposed when its 2023–24 score is ${data.config.TEST_MIN} or higher. A contact notice is drafted when the faecal or pathogen score is ${data.config.ADVISORY_MIN} or higher. Sampling covers the ${data.config.WINDOW_DAYS} days after the rain. Changing the visit budget never changes the scores or the order.</p><p><strong>Why ${data.config.RAIN_MM} mm?</strong> ${data.config.RAIN_MM===20?`It matches the WMO/ETCCDI “very heavy precipitation day” index (R20mm: daily rain of at least 20 mm; ${link('https://etccdi.pacificclimate.org/list_27_indices.shtml','ETCCDI index list')}).`:'It is a configurable daily total.'} Our rain data are daily totals, so hourly intensity (for example the 7.6 mm per hour heavy-rain rate) can't be checked. Each city should calibrate the trigger locally.</p>`;
  }
  function render(){
    const {city,plan,allocated}=view();
    $('budget-error').hidden=true;$('budget').removeAttribute('aria-invalid');
    $('mode-live').setAttribute('aria-pressed',String(mode==='live'));
    $('mode-replay').setAttribute('aria-pressed',String(mode==='replay'));
    const ref=data.sources[`forecasts/${cityId}.json`];
    $('fetched-at').textContent=mode==='live'?`Latest saved forecast fetched ${niceTime(ref?.fetched_at)}`:'Past rainfall from the OneAquaHealth archive';
    $('budget').max=String(plan.sites.length);$('budget').value=String(budget);
    $('budget-minus').disabled=budget===0;$('budget-plus').disabled=budget===plan.sites.length;
    const range=$('budget-range');range.max=String(Math.max(plan.ranking.length,budget,1));range.value=String(budget);range.setAttribute('aria-valuetext',`${budget} site visits`);
    renderWeather(city,plan,allocated);renderVisits(plan,allocated);renderProtection(plan,allocated);renderDecision(city,plan,allocated);renderNotices(plan);renderReview(plan);renderTracker(plan,allocated);renderSummaryBar(city,plan,allocated);renderNext(city,plan,allocated);renderRoster(plan,allocated);renderCoverage(plan);renderMap(city,plan,allocated);renderSources();
    $('plan-status').textContent=`${city.name} · ${mode==='live'?'latest saved forecast':plan.label} · ${allocated.size} visits proposed · ${plan.notices.length} draft notices requiring coordinator review`;
    history.replaceState(null,'',`?city=${encodeURIComponent(cityId)}&mode=${mode}&visits=${budget}${location.hash}`);
  }
  function applyBudget(value){
    const maximum=data.cities[cityId].modes[mode].sites.length;
    if(!Number.isInteger(value)||value<0||value>maximum){$('budget-error').textContent=`Enter a whole number from 0 to ${maximum}.`;$('budget-error').hidden=false;$('budget').setAttribute('aria-invalid','true');return;}
    budget=value;$('budget-error').hidden=true;$('budget').removeAttribute('aria-invalid');render();
  }
  function changeMode(value){mode=value;render();}
  async function start(){
    try{
      const response=await fetch('data/plan.json',{cache:'no-store'});
      if(!response.ok) throw new Error('The saved plan could not be loaded.');
      data=await response.json();
      if(data.schema_version!==1||!data.cities||!data.config) throw new Error('The saved plan has an unsupported format.');
      filed=null;
      try{
        const filedResponse=await fetch('data/filed.json',{cache:'no-store'});
        if(filedResponse.ok) filed=await filedResponse.json();
      }catch(_error){filed=null;}
      const params=new URLSearchParams(location.search);
      if(params.has('city')&&Object.hasOwn(data.cities,params.get('city'))) cityId=params.get('city');
      else if(!params.has('city')&&Object.hasOwn(data.cities,'CO')) cityId='CO';
      else cityId=Object.hasOwn(data.cities,'OS')?'OS':Object.keys(data.cities)[0];
      mode=params.has('mode')?(params.get('mode')==='replay'?'replay':'live'):'replay';
      const proposed=params.has('visits')?Number(params.get('visits')):data.config.VISITS_PER_CITY;
      const maximum=data.cities[cityId].modes[mode].sites.length;
      budget=Number.isInteger(proposed)&&proposed>=0?Math.min(proposed,maximum):Math.min(data.config.VISITS_PER_CITY,maximum);
      $('city-select').innerHTML=Object.entries(data.cities).map(([id,city])=>`<option value="${escapeHTML(id)}">${escapeHTML(city.name)}</option>`).join('');$('city-select').value=cityId;
      $('city-pills').innerHTML=Object.entries(data.cities).map(([id,city])=>`<button type="button" class="pill" data-city="${escapeHTML(id)}" aria-pressed="false">${escapeHTML(city.name)}<i class="storm-dot" aria-hidden="true"></i></button>`).join('');
      $('city-pills').addEventListener('click',e=>{const b=e.target.closest('[data-city]');if(!b)return;$('city-select').value=b.dataset.city;$('city-select').dispatchEvent(new Event('change'));b.focus();});
      const allSites=Object.values(data.cities).flatMap(c=>c.modes.live.sites), labSites=allSites.filter(s=>s.source_health);
      $('evidence-age').textContent=`Based on ${labSites.length} lab records from 2023–24.`;
      $('data-stamp').textContent=`Roster fetched ${timestamp(data.sources['sites.json']?.fetched_at)}`;
      $('app').hidden=false;initializeMap();
      $('city-select').addEventListener('change',()=>{cityId=$('city-select').value;budget=Math.min(budget,data.cities[cityId].modes[mode].sites.length);render();});
      $('mode-live').addEventListener('click',()=>changeMode('live'));$('mode-replay').addEventListener('click',()=>changeMode('replay'));
      $('budget').addEventListener('input',()=>applyBudget($('budget').value===''?NaN:Number($('budget').value)));
      $('budget').addEventListener('blur',()=>{if($('budget').hasAttribute('aria-invalid')){$('budget').value=String(budget);$('budget').removeAttribute('aria-invalid');$('budget-error').hidden=true;}});
      $('budget-minus').addEventListener('click',()=>applyBudget(budget-1));$('budget-range').addEventListener('input',()=>applyBudget(Number($('budget-range').value)));
      $('visits').addEventListener('mouseover',e=>{const c=e.target.closest('.visit-card');highlight(c?c.dataset.code:null);});$('visits').addEventListener('mouseleave',()=>highlight(null));
      $('visits').addEventListener('focusin',e=>{const c=e.target.closest('.visit-card');if(c)highlight(c.dataset.code);});$('budget-plus').addEventListener('click',()=>applyBudget(budget+1));
      $('download-fhir').addEventListener('click',downloadFhir);
      $('export-review').addEventListener('click',exportReview);
      $('import-review').addEventListener('click',()=>$('review-file').click());
      $('review-file').addEventListener('change',event=>{importReview(event.target.files?.[0]);event.target.value='';});
      $('open-guide').addEventListener('click',event=>openGuide(event.currentTarget));
      $('guide-skip').addEventListener('click',closeGuide);
      $('guide-back').addEventListener('click',()=>{guideIndex=Math.max(0,guideIndex-1);showGuideStep();});
      $('guide-next').addEventListener('click',()=>{if(guideIndex===GUIDE_STEPS.length-1)closeGuide();else{guideIndex++;showGuideStep();}});
      document.addEventListener('keydown',guideKeys);
      window.addEventListener('resize',()=>{if(!$('guide').hidden)positionGuide();});
      $('print-all-cards').addEventListener('click',()=>printTaskCards(view().plan.ranking.slice(0,budget)));
      document.addEventListener('click',event=>{
        const button=event.target.closest('[data-card-lang]');
        if(!button) return;
        document.querySelectorAll('.task-card').forEach(saveCitizenCard);
        const open=[...document.querySelectorAll('.task-card[open]')].map(card=>card.dataset.code);
        cardLangChoice[cityId]=button.dataset.cardLang==='en'?'en':(CITY_LANG[cityId]||'en');
        render();
        open.forEach(code=>{const card=document.querySelector(`.task-card[data-code="${CSS.escape(code)}"]`);if(card) card.open=true;});
      });
      document.addEventListener('click',event=>{const button=event.target.closest('[data-print-card]');if(!button)return;printTaskCards([button.dataset.printCard]);});
      document.addEventListener('change',event=>{const card=event.target.closest('.task-card');if(card&&event.target.matches('input'))saveCitizenCard(card);const confirm=event.target.closest('[data-confirm-date]');if(confirm)saveConfirmDate(confirm);});
      document.addEventListener('input',event=>{const card=event.target.closest('.task-card');if(card&&event.target.matches('[data-q-text]'))saveCitizenCard(card);});
      document.addEventListener('click',event=>{const button=event.target.closest('[data-cover-notices]');if(!button)return;const visits=Number(button.dataset.coverNotices);applyBudget(visits);$('plan-status').textContent=`Visit budget is now ${visits}, which covers every notice site. The visit order is unchanged.`;});
      document.addEventListener('click',e=>{const b=e.target.closest('[data-review]');if(b){setReview(b.dataset.review,b.dataset.code,b.dataset.val);return;}if(e.target.closest('[data-clear-review]')){const pre=`${cityId}|${mode}|`;Object.keys(reviews).filter(k=>k.startsWith(pre)).forEach(k=>delete reviews[k]);try{localStorage.setItem(REVIEW_KEY,JSON.stringify(reviews));}catch{}render();$('plan-status').textContent='Review cleared for this city and mode.';}});
      document.addEventListener('click',e=>{const sg=e.target.closest('[data-seg]');if(!sg)return;const code=sg.dataset.seg;if($(`visit-${code}`))focusCard(code);else{const m=markers.get(code);if(m){leafletMap.panTo(m.getLatLng());m.openPopup();$('map').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});}}});
      document.addEventListener('pointermove',e=>{const c=e.target.closest('.visit-card,#notices>.notice-row,.surface.protection,.kpi');if(!c)return;const r=c.getBoundingClientRect();c.style.setProperty('--mx',`${e.clientX-r.left}px`);c.style.setProperty('--my',`${e.clientY-r.top}px`);},{passive:true});
      $('download-lab').addEventListener('click',downloadLabSheet);
      document.addEventListener('click',e=>{if(e.target.closest('[data-sb-lab]')){downloadLabSheet();return;}if(e.target.closest('[data-sb-download]')){downloadFhir();return;}if(e.target.closest('[data-sb-top]')){window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});return;}const j=e.target.closest('#header-status [data-jump]');if(j)jumpTo(j.dataset.jump);});
      const SHEETS='details.task-card,details.why';
      const syncSheets=()=>document.body.classList.toggle('sheet-open',!!document.querySelector('details.task-card[open],details.why[open]'));
      document.addEventListener('toggle',e=>{const d=e.target;if(!(d instanceof HTMLDetailsElement)||!d.matches(SHEETS))return;
        if(d.open){document.querySelectorAll(SHEETS).forEach(o=>{if(o!==d&&o.open)o.open=false;});requestAnimationFrame(()=>d.querySelector('.sheet-close')?.focus({preventScroll:true}));}
        else if(d.isConnected&&!document.querySelector(SHEETS.split(',').map(x=>x+'[open]').join(','))) d.querySelector('summary')?.focus({preventScroll:true});
        syncSheets();},true);
      document.addEventListener('click',e=>{
        if(e.target.closest('[data-mode-live]')){changeMode('live');return;}
        const close=e.target.closest('[data-close-sheet]');if(close){const d=close.closest('details');if(d)d.open=false;return;}
        if(e.target.matches&&e.target.matches('details.task-card[open],details.why[open]')){e.target.open=false;}
      });
      document.addEventListener('keydown',e=>{if(e.key==='Escape'){const d=document.querySelector('details.task-card[open],details.why[open]');if(d){d.open=false;e.preventDefault();}}});
      $('decision').addEventListener('click',event=>{const step=event.target.closest('[data-jump]');if(step)jumpTo(step.dataset.jump);});
      document.addEventListener('click',event=>{const button=event.target.closest('[data-locate]');if(!button)return;if(page!=='plan'){goPage('plan');setTimeout(()=>button.isConnected?button.click():null,60);}const marker=markers.get(button.dataset.locate);if(!marker)return;leafletMap.panTo(marker.getLatLng());marker.openPopup();$('map').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});});
      render();$('loading').hidden=true;
      // Deep links: #card-C5 opens that citizen task card, #notice-C16 opens that notice.
      const openFromHash=()=>{const m=location.hash.match(/^#(card|notice)-([A-Za-z0-9_-]+)$/);if(!m)return;
        const el=m[1]==='card'?$(`visit-${m[2]}`)?.querySelector('details.task-card'):document.querySelector(`#notices .notice-row[data-code="${CSS.escape(m[2])}"] details.notice-more`);
        if(!el)return;el.open=true;if(m[1]==='notice')el.closest('.notice-row').scrollIntoView({block:'start'});};
      setPage(pageFromHash(),{scroll:false});openFromHash();
      if(!GUIDE_SUPPRESSED&&!localStorage.getItem(GUIDE_KEY)) openGuide($('open-guide'));
      const onRoute=()=>{setPage(pageFromHash(),{scroll:!location.hash.match(/^#(card|notice)-/)});openFromHash();};
      window.addEventListener('hashchange',onRoute);window.addEventListener('popstate',onRoute);
    }catch(error){$('app').hidden=true;$('loading').hidden=true;$('fatal').hidden=false;$('fatal').innerHTML=`<strong>Sampling plan unavailable</strong><p>${escapeHTML(error.message)}</p><p>Serve the web folder with the local Python web server, then reload this page. See docs/changes/readmeUI.md for the command.</p>`;}
  }
  document.addEventListener('DOMContentLoaded',start,{once:true});
