/* 법원직.com — 멀티과목 SPA (민법위키 하랑재와 동일 틀)
   과목별 데이터: window.CIVPROC/LAWTEXT/NOTES (민소), window.CRIMPROC/CRIMLAWTEXT/CRIMNOTES (형소) ... */
(function () {
  "use strict";
  var SUBJECTS = ["헌법", "민법", "민사소송법", "형법", "형사소송법", "상법", "부동산등기법"];
  var REG = {};
  function reg(name, slug, d, l, n){ if(window[d]) REG[name] = {name:name, slug:slug, data:window[d], lt:window[l]||{}, nt:window[n]||{desc:{},cases:{},gist:{}}}; }
  reg("헌법","constitution","CONST","CONSTLAWTEXT","CONSTNOTES");
  reg("민법","civil","CIVIL","CIVILLAWTEXT","CIVILNOTES");
  reg("민사소송법","civ-proc","CIVPROC","LAWTEXT","NOTES");
  reg("형사소송법","crim-proc","CRIMPROC","CRIMLAWTEXT","CRIMNOTES");
  reg("형법","penal","PENAL","PENALLAWTEXT","PENALNOTES");
  var DEFAULT_SUB = REG["민법"] ? "민법" : (Object.keys(REG)[0]||"민법");

  function esc(s){ return (s==null?"":String(s)).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c];}); }
  function el(sel){ return document.querySelector(sel); }
  var MEM={};
  var store={
    get:function(k,d){ if(Object.prototype.hasOwnProperty.call(MEM,k)) return MEM[k]; try{ var v=localStorage.getItem("bwj_"+k); var r=(v==null)?d:JSON.parse(v); MEM[k]=r; return r; }catch(e){ return d; } },
    set:function(k,v){ MEM[k]=v; try{ localStorage.setItem("bwj_"+k,JSON.stringify(v)); }catch(e){} }
  };
  function shuffle(a){ a=a.slice(); for(var i=a.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=a[i];a[i]=a[j];a[j]=t;} return a; }

  var JIMUN=["","ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ"];
  function fmtSrc(s){
    if(!s) return ""; s=String(s);
    var bm=s.match(/변시\s*0*(\d+)/);
    if(bm){
      var bq=s.match(/문\s*0*(\d+)/);
      var bu=s.match(/(?:보기\s*)?([ㄱ-ㅎ]|[①-⑳]|[1-5])\s*$/);
      var bout="변시"+bm[1];
      if(bq) bout+=" "+bq[1]+"번";
      if(bu && !/문\s*0*\d+\s*$/.test(s)) bout+=" "+bu[1];
      return bout;
    }
    var ym=s.match(/(\d{4})\s*(상|하|하반기|a|b|A|B)?/);
    var half=""; if(ym&&ym[2]){ var c=ym[2].toLowerCase(); half=(c==="상"||c==="a")?"상":((c==="하"||c==="하반기"||c==="b")?"하":""); }
    var q=s.match(/(?:문\s*0*)?(\d+)\s*번/)||s.match(/문\s*0*(\d+)/);
    var sub=s.match(/([①-⑳]|[ㄱ-ㅎ])\s*$/)||s.match(/-\s*(\d+)/);
    if(!ym&&!q) return s;
    var out="법원직";
    if(ym) out+=ym[1].slice(2)+(half?half:"년");
    if(q) out+=q[1]+"번";
    if(sub){ var n=+sub[1]; out+=isNaN(n)?sub[1]:((n>=1&&n<=20)?String.fromCharCode(0x245F+n):("("+n+")")); }
    out+=" 기출";
    return out;
  }
  function srcChips(sources, max){
    var a=(sources||[]).filter(Boolean); var h="";
    a.slice(0,max||4).forEach(function(s){ h+='<span class="chip">'+esc(fmtSrc(s))+'</span>'; });
    if(a.length>(max||4)) h+='<span class="ref">+'+(a.length-(max||4))+'</span>';
    return h;
  }
  function famChips(families){
    return (families||[]).filter(function(f){ return f!=="법원직" && f!=="변호사시험"; }).map(function(f){ return '<span class="chip">'+esc(f)+'</span>'; }).join("");
  }
  function refExtra(at){
    var ref=at&&at.ref?String(at.ref):"";
    if(!ref) return "";
    if(/^(변시|20\d{2}\s*법원직)/.test(ref)) return "";
    return '<span class="ref">· '+linkifyRef(ref)+'</span>';
  }
  function linkifyRef(s){
    s=esc(s||"");
    return s.replace(/(\d{2,4}[가-힣]{1,3}\d+)/g, function(m){ return '<a href="https://casenote.kr/대법원/'+encodeURIComponent(m)+'" target="_blank" rel="noopener" class="caselink">'+m+'</a>'; });
  }

  function getScores(){ return store.get("scores",[]); }
  function addScore(rec){ var a=getScores(); a.push(rec); a.sort(function(x,y){return y.score-x.score;}); a=a.slice(0,50); store.set("scores",a); return a; }
  function boardHTML(limit){
    var a=getScores().slice(0,limit||10);
    if(!a.length) return '<div class="ref" style="padding:10px">아직 기록이 없어요. CBT를 풀고 첫 고득점에 도전하세요!</div>';
    var medal=["🥇","🥈","🥉"];
    var h='<table class="lb"><thead><tr><th>#</th><th>닉네임</th><th>점수</th><th>정답률</th><th>범위</th><th>날짜</th></tr></thead><tbody>';
    a.forEach(function(r,i){ h+='<tr'+(i<3?' class="top"':'')+'><td>'+(medal[i]||(i+1))+'</td><td>'+esc(r.name)+'</td><td>'+r.score+'</td><td>'+r.pct+'%</td><td>'+esc(r.scope||"-")+'</td><td>'+esc(r.date)+'</td></tr>'; });
    h+='</tbody></table>'; return h;
  }

  // 현재 과목 컨텍스트
  var D, LT, NT, CURSUB;
  function use(sub){ var s=REG[sub]||REG[DEFAULT_SUB]; D=s.data; LT=s.lt; NT=s.nt; CURSUB=s.name; return s; }
  function readySubs(){ return Object.keys(REG); }
  function quizSubs(){ return Object.keys(REG).filter(function(n){return (REG[n].data.ox||[]).length;}); }

  function route(){
    var raw=location.hash.replace(/^#/,"")||"/";
    var sp=raw.split("?"); var path=sp[0]; var params=new URLSearchParams(sp[1]||"");
    var parts=path.split("/").filter(Boolean);
    var r={view:"home"};
    if(parts[0]==="sub"){ r.view="sub"; r.sub=decodeURIComponent(parts[1]||""); r.art=parts[2]?decodeURIComponent(parts[2]):null; }
    else if(parts[0]==="cbt"){ r.view="cbt"; r.sub=params.get("sub"); r.art=params.get("art"); r.pyeon=params.get("pyeon"); r.scope=params.get("scope"); }
    else if(parts[0]==="board"){ r.view="board"; }
    else if(parts[0]==="news"){ r.view="news"; }
    return r;
  }

  function renderNav(r){
    var h="";
    SUBJECTS.forEach(function(s){
      var on=(r.view==="sub"&&r.sub===s)?"active":"";
      var rdy=REG[s]?'':' style="opacity:.6"';
      h+='<a class="'+on+'"'+rdy+' href="#/sub/'+encodeURIComponent(s)+'">'+esc(s)+'</a>';
    });
    h+='<span class="sep"></span>';
    h+='<a class="feat'+(r.view==="cbt"?" active":"")+'" href="#/cbt">🎮 CBT 게임센터</a>';
    h+='<a class="'+(r.view==="board"?"active":"")+'" href="#/board">자유게시판</a>';
    h+='<a class="'+(r.view==="news"?"active":"")+'" href="#/news">뉴스</a>';
    el("#nav").innerHTML=h;
  }

  function grouped(){
    var map=new Map();
    (D.tree||[]).forEach(function(p){ map.set(p.pyeon,{pyeon:p.pyeon,jangs:p.jangs.map(function(j){return {jang:j.jang,arts:[]};})}); });
    D.articles.forEach(function(a){
      var pg=map.get(a.pyeon); if(!pg){ pg={pyeon:a.pyeon,jangs:[]}; map.set(a.pyeon,pg); }
      var jg=null; for(var i=0;i<pg.jangs.length;i++){ if(pg.jangs[i].jang===a.jang){ jg=pg.jangs[i]; break; } }
      if(!jg){ jg={jang:a.jang,arts:[]}; pg.jangs.push(jg); }
      jg.arts.push(a);
    });
    var out=[]; map.forEach(function(p){ p.jangs=p.jangs.filter(function(j){return j.arts.length;}); if(p.jangs.length) out.push(p); });
    return out;
  }
  function artTitle(k){ return LT[k]?LT[k].title:""; }
  function artLabel(k,a){ var t=artTitle(k); if(t) return t; if(a&&a.atoms&&a.atoms[0]) return a.atoms[0].o.slice(0,18)+"…"; return ""; }
  function subPath(art){ return '#/sub/'+encodeURIComponent(CURSUB)+(art?'/'+encodeURIComponent(art):''); }

  function tocHTML(activeArt){
    var g=grouped(); var h='<h3>'+esc(CURSUB)+' · 목차</h3>';
    g.forEach(function(p){
      var hasActive=p.jangs.some(function(j){return j.arts.some(function(a){return a.art===activeArt;});});
      h+='<div class="pyeon"><button data-toggle>'+(hasActive?"▾":"▸")+' '+esc(p.pyeon)+'</button>';
      h+='<div class="pbody'+(hasActive?"":" hide")+'">';
      p.jangs.forEach(function(j){
        if(j.jang && j.jang!==p.pyeon && !/^(재심|독촉|공시|판결의|재판의|관련)/.test(j.jang)) h+='<div class="jang">'+esc(j.jang)+'</div>';
        h+='<div class="arts">';
        j.arts.forEach(function(a){
          var on=a.art===activeArt?"active":"";
          h+='<a class="'+on+'" href="'+subPath(a.art)+'" title="'+esc(artLabel(a.art,a))+'">'+esc(a.art)+(a.count>0?'<span class="c">'+a.count+(a.freqMax>=2?" ★":"")+'</span>':'')+'</a>';
        });
        h+='</div>';
      });
      h+='</div></div>';
    });
    return h;
  }
  function bindToc(){
    document.querySelectorAll(".toc [data-toggle]").forEach(function(b){
      b.addEventListener("click",function(){
        var body=b.nextElementSibling; body.classList.toggle("hide");
        b.textContent=(body.classList.contains("hide")?"▸":"▾")+b.textContent.slice(1);
      });
    });
  }

  function renderSubjectHome(c){
    var s=D.stats||{}; var g=grouped(); var hasOX=(D.ox||[]).length>0;
    var reviewPending = D.review && /review/.test(D.review.status || "");
    var heroText = hasOX
      ? (reviewPending
          ? '법원직 9급 기출 OX를 조문별로 정리합니다. 2025 회차 seed 구축 완료 · 현행법 검증 진행 중.'
          : (CURSUB === "헌법"
              ? '법원직 9급 기출 OX를 조문별로 정리하고, CBT 게임센터에서 풀이합니다. 2006–2025 · 2006은 공개 문제와 법리검토 기준 반영.'
              : '법원직 9급 기출 OX를 조문별로 정리하고, CBT 게임센터에서 풀이합니다. 2007–2025 · 공식 확정정답표 검증완료.'))
      : '조문 본문을 편·장별로 완비했습니다. 기출 OX(CBT)는 순차 적재 중입니다.';
    var h='<div class="main">';
    h+='<div class="hero"><h1>'+esc(CURSUB)+'</h1><p>'+heroText+'</p>';
    h+='<div class="stat-row">'
      +'<div class="stat"><b>'+(s.articles||0)+'</b><span>조문</span></div>'
      +'<div class="stat"><b>'+(s.atoms||0)+'</b><span>통합 법리</span></div>'
      +'<div class="stat"><b>'+(s.ox||0)+'</b><span>OX 문항</span></div>'
      +'<div class="stat"><b>'+(s.freq||0)+'</b><span>★ 빈출</span></div></div></div>';
    if(hasOX) h+='<div class="cta"><div><div class="big">바로 CBT 게임센터에서 풀어보기</div><div class="sm">전체 '+(s.ox||0)+'문항 · 빈출만/편별/조문별 필터 · 고득점 랭킹</div></div><a class="btn-play" href="#/cbt?sub='+encodeURIComponent(CURSUB)+'">🎮 OX 풀기</a></div>';
    else h+='<div class="cta"><div><div class="big">기출 OX 준비 중</div><div class="sm">현재 조문 본문·목차 완비. 법원직 9급 '+esc(CURSUB)+' 기출 OX를 순차 적재합니다.</div></div></div>';
    h+='<div class="sect-h"><b>편별 보기</b><span>조문을 눌러 본문·해설 확인</span></div><div class="grid-pyeon">';
    g.forEach(function(p){
      var artsAll=[]; p.jangs.forEach(function(j){ artsAll=artsAll.concat(j.arts); });
      var first=artsAll[0]; var ox=0; artsAll.forEach(function(a){ ox+=a.count; });
      h+='<div class="pcard"><h4><a href="'+subPath(first.art)+'">'+esc(p.pyeon)+'</a></h4>';
      p.jangs.forEach(function(j){
        var cnt=0; j.arts.forEach(function(a){cnt+=a.count;});
        var label=(j.jang&&!/^(재심|독촉|공시|판결의|재판의|관련)/.test(j.jang)&&j.jang!==p.pyeon)?j.jang:"조문";
        h+='<div class="jl">'+esc(label)+' · '+j.arts.length+'개 조문'+(cnt?' · OX '+cnt:'')+'</div>';
      });
      h+='</div>';
    });
    h+='</div></div>';
    c.innerHTML='<div class="wrap"><aside class="toc">'+tocHTML(null)+'</aside>'+h+'</div>';
    bindToc();
  }

  function findArt(k){ for(var i=0;i<D.articles.length;i++){ if(D.articles[i].art===k) return D.articles[i]; } return null; }
  function renderArticle(c,r){
    var a=findArt(r.art);
    if(!a){ renderSubjectHome(c); return; }
    var lt=LT[r.art]; var nO=0, nX=0, fr=0;
    a.atoms.forEach(function(at){ if(at.ans==="X") nX++; else nO++; if(at.x) nX+=at.x.length; if(at.freq>=2)fr++; });
    var h='<div class="main">';
    h+='<div class="crumb">'+esc(CURSUB)+' › '+esc(a.pyeon)+' › '+esc(a.jang)+'</div>';
    h+='<div class="h-art"><h1>'+esc(r.art)+'</h1>'+(lt?'<span class="sub">'+esc(lt.title||a.title||"")+'</span>':(a.title?'<span class="sub">'+esc(a.title)+'</span>':''))+'</div>';
    if(lt&&lt.body){ h+='<div class="lawbox"><div class="t">조문</div>'+esc(lt.body).replace(/\n/g,"<br>")+'</div>'; }
    else { h+='<div class="lawbox" style="color:var(--ink3)">조문 본문은 순차 적재 중입니다.</div>'; }
    if(NT.desc[r.art]){ h+='<div class="sect-h"><b>조문 해설</b><span>실무제요 참고 · 원문 비복제</span></div><div class="desc">'+NT.desc[r.art]+'</div>'; }
    (NT.cases[r.art]||[]).forEach(function(cn){ var g=NT.gist[cn]; if(!g) return;
      h+='<div class="casebox"><div class="ct"><span class="cb-no"><a href="'+g.url+'" target="_blank" rel="noopener">'+esc(cn)+'</a></span> <span class="cb-meta">'+esc(g.court)+' '+esc(g.date)+' · '+esc(g.name)+'</span></div><div class="cb-gist">'+esc(g.gist)+'</div><a class="cb-link" href="'+g.url+'" target="_blank" rel="noopener">원문 보기 →</a></div>'; });
    if(a.atoms.length){
    h+='<div class="cta"><div><div class="big">이 조문 기출 OX '+(nO+nX)+'문항</div><div class="sm">O 대표 atom '+nO+' · 종속 X '+nX+(fr?' · ★ 빈출 '+fr:'')+'</div></div>'
      +'<a class="btn-play" href="#/cbt?sub='+encodeURIComponent(CURSUB)+'&art='+encodeURIComponent(r.art)+'">🎮 이 조문 풀기</a></div>';
    h+='<div class="sect-h"><b>조문별 기출 atom</b><span>O 대표 atom 아래에 X 함정 종속 · 법원직/변호사시험 출처</span></div>';
    a.atoms.slice().sort(function(x,y){return (y.weight||0)-(x.weight||0) || (y.freq||1)-(x.freq||1);}).forEach(function(at){
      var ans=(at.ans==="X")?"X":"O", tag=(ans==="X")?"tag-x":"tag-o";
      h+='<div class="card"><div class="row"><span class="'+tag+'">'+ans+'</span><div style="flex:1;min-width:0">';
      h+='<div class="stmt">'+esc(at.o)+'</div>';
      h+='<div class="meta">'+famChips(at.sourceFamilies)+(at.freq>=2?'<span class="badge-star">★ 빈출 '+at.freq+'회</span>':'')+srcChips(at.sources,6)+refExtra(at)+(at.verified?'<span class="chip-v">✓ 검증</span>':'')+'</div>';
      (at.x||[]).forEach(function(xx){
        h+='<div class="trap"><span class="tag-x" style="padding:1px 7px;font-size:11px">함정 X</span> <span style="font-size:13px;color:var(--ink2)">'+esc(xx.q)+'</span> '+famChips(xx.sourceFamilies)+srcChips(xx.sources||(xx.src?[xx.src]:[]),4)+'</div>';
      });
      h+='</div></div></div>';
    });
    } else { h+='<div class="ref" style="margin-top:12px">이 조문은 기출 OX가 없습니다.</div>'; }
    h+='</div>';
    c.innerHTML='<div class="wrap"><aside class="toc">'+tocHTML(r.art)+'</aside>'+h+'</div>';
    bindToc();
    var act=document.querySelector(".toc a.active"); if(act && act.scrollIntoView) act.scrollIntoView({block:"center"});
  }

  function renderPlaceholder(c,sub){
    c.innerHTML='<div class="wrap single"><div class="ph"><h2>'+esc(sub)+' — 준비 중</h2><p>민사소송법과 동일한 틀(조문 위키 + CBT 게임센터)로 추가됩니다.<br>현재 <a href="#/sub/민사소송법">민사소송법</a>은 완성, <a href="#/sub/형사소송법">형사소송법</a>은 조문 완비 단계입니다.</p></div></div>';
  }

  // ===== CBT =====
  var game=null;
  function poolFor(opts){
    var src=(REG[opts.sub]||REG[DEFAULT_SUB]).data.ox||[];
    var pool=src.slice();
    if(opts.art) pool=pool.filter(function(o){return o.art===opts.art;});
    else if(opts.pyeon) pool=pool.filter(function(o){return o.pyeon===opts.pyeon;});
    if(opts.scope==="wrong"){ var w=store.get("wrong",[]); var set={}; w.forEach(function(id){set[id]=1;}); pool=pool.filter(function(o){return set[o.id];}); }
    if(opts.freqOnly) pool=pool.filter(function(o){return o.freq>=2;});
    return pool;
  }
  function renderCBT(c,r){
    if(game&&game.active){ drawGame(c); return; }
    var qs=quizSubs();
    if(!qs.length){ c.innerHTML='<div class="wrap single"><div class="ph"><h2>CBT 게임센터</h2><p>아직 적재된 기출 OX가 없습니다.</p></div></div>'; return; }
    var sub=(r.sub&&qs.indexOf(r.sub)>=0)?r.sub:(qs.indexOf(DEFAULT_SUB)>=0?DEFAULT_SUB:qs[0]);
    var SD=REG[sub].data;
    var opts={sub:sub,art:r.art||null,pyeon:r.pyeon||null,scope:r.scope||"all",freqOnly:false,count:20};
    var avail=poolFor(opts).length;
    var wrongN=store.get("wrong",[]).length;
    var pyeonOpts=(SD.tree||[]).map(function(p){return p.pyeon;});
    var h='<div class="cbt-wrap"><div class="cbt-setup">';
    h+='<h2>🎮 CBT 게임센터</h2><p style="color:var(--ink2);margin:4px 0 0">'+esc(sub)+' 기출 OX '+((SD.stats&&SD.stats.ox)||0)+'문항 · 맞히면 콤보가 쌓입니다.</p>';
    if(qs.length>1){ h+='<div class="field"><label>과목</label><div class="opts" id="subsel">'; qs.forEach(function(n){ h+='<button class="opt'+(n===sub?" on":"")+'" data-sub="'+esc(n)+'">'+esc(n)+'</button>'; }); h+='</div></div>'; }
    h+='<div class="field"><label>범위</label><div class="opts" id="scope">'
      +'<button class="opt on" data-scope="all">전체</button>'
      +'<button class="opt" data-scope="wrong">오답노트 ('+wrongN+')</button></div></div>';
    h+='<div class="field"><label>편 선택 (선택)</label><div class="opts" id="pyeon">'
      +'<button class="opt'+(!opts.pyeon?" on":"")+'" data-pyeon="">전체 편</button>';
    pyeonOpts.forEach(function(p){ h+='<button class="opt'+(opts.pyeon===p?" on":"")+'" data-pyeon="'+esc(p)+'">'+esc(p.replace(/^제\d편 /,""))+'</button>'; });
    h+='</div></div>';
    if(opts.art) h+='<div class="field"><label>조문</label><div class="opts"><button class="opt on">'+esc(opts.art)+'</button><button class="opt" data-clearart>해제</button></div></div>';
    h+='<div class="field"><label>옵션</label><div class="opts"><button class="opt" id="freq">★ 빈출만</button></div></div>';
    h+='<div class="field"><label>문항 수</label><div class="opts" id="count">'
      +'<button class="opt" data-count="10">10</button><button class="opt on" data-count="20">20</button>'
      +'<button class="opt" data-count="50">50</button><button class="opt" data-count="0">전체</button></div></div>';
    h+='<div style="margin-top:18px"><button class="btn-play" id="start" style="width:100%;justify-content:center">시작하기 <span id="availn">('+avail+'문항)</span></button></div>';
    h+='</div>';
    h+='<div class="cbt-setup" style="margin-top:12px"><div class="sect-h"><b>🏆 고득점</b><span>이 브라우저 기준 · Supabase 연결 시 전체 공유 랭킹</span></div>'+boardHTML(10)+'</div>';
    h+='</div>';
    c.innerHTML=h;

    var cur={sub:sub,art:opts.art||null,pyeon:"",scope:"all",freqOnly:false,count:20};
    function refresh(){ el("#availn").textContent="("+poolFor(cur).length+"문항)"; }
    function sel(box,b){ el(box).querySelectorAll(".opt").forEach(function(x){x.classList.remove("on");}); b.classList.add("on"); }
    var ss=el("#subsel"); if(ss) ss.addEventListener("click",function(e){ var b=e.target.closest("[data-sub]"); if(!b)return; location.hash="#/cbt?sub="+encodeURIComponent(b.getAttribute("data-sub")); });
    el("#scope").addEventListener("click",function(e){ var b=e.target.closest("[data-scope]"); if(!b)return; cur.scope=b.getAttribute("data-scope"); sel("#scope",b); refresh(); });
    el("#pyeon").addEventListener("click",function(e){ var b=e.target.closest("[data-pyeon]"); if(!b)return; cur.pyeon=b.getAttribute("data-pyeon"); cur.art=null; sel("#pyeon",b); refresh(); });
    el("#count").addEventListener("click",function(e){ var b=e.target.closest("[data-count]"); if(!b)return; cur.count=parseInt(b.getAttribute("data-count"),10); sel("#count",b); });
    el("#freq").addEventListener("click",function(){ cur.freqOnly=!cur.freqOnly; el("#freq").classList.toggle("on",cur.freqOnly); refresh(); });
    var ca=document.querySelector("[data-clearart]"); if(ca) ca.addEventListener("click",function(){ location.hash="#/cbt?sub="+encodeURIComponent(sub); });
    el("#start").addEventListener("click",function(){ startGame(cur); });
  }
  function scopeLbl(cur){ var t=(REG[cur.sub]?cur.sub.replace("법",""):""); if(cur.art) return t+"·"+cur.art; if(cur.scope==="wrong") return "오답노트"; if(cur.pyeon) return t+"·"+cur.pyeon.replace(/^제\d편 /,""); return t+(cur.freqOnly?"·빈출":"·전체"); }
  function startGame(cur){
    var pool=poolFor(cur);
    if(!pool.length){ alert("해당 범위에 문항이 없습니다."); return; }
    pool=shuffle(pool); if(cur.count>0) pool=pool.slice(0,cur.count);
    game={pool:pool,i:0,score:0,combo:0,maxcombo:0,wrong:[],answered:false,active:true,scope:scopeLbl(cur)};
    drawGame(el("#content"));
  }
  function drawGame(c){
    var g=game; if(g.i>=g.pool.length){ drawEnd(c); return; }
    var q=g.pool[g.i];
    var srcline=(q.sources||[]).filter(Boolean).map(fmtSrc).join(" · ");
    var h='<div class="cbt-wrap">';
    h+='<div class="scorebar"><div class="sb"><b>'+(g.i+1)+'/'+g.pool.length+'</b><span>진행</span></div>'
      +'<div class="sb"><b>'+g.score+'</b><span>점수</span></div>'
      +'<div class="sb"><b>🔥'+g.combo+'</b><span>콤보</span></div></div>';
    h+='<div class="q-card"><div class="q-top"><span>CBT 풀이</span><span class="flame">최고 콤보 '+g.maxcombo+'</span></div>';
    h+='<div class="q-art">'+(srcline?'<b>'+esc(srcline)+'</b>':esc(q.art))+(q.freq>=2?' · ★빈출':'')+'</div>';
    h+='<div class="q-stmt">'+esc(q.stmt)+'</div>';
    h+='<div class="ox-btns"><button class="b-o" data-ans="O">O (맞다)</button><button class="b-x" data-ans="X">X (틀리다)</button></div>';
    h+='<div id="rv"></div></div></div>';
    c.innerHTML=h;
    g.answered=false;
    c.querySelectorAll("[data-ans]").forEach(function(b){ b.addEventListener("click",function(){ answer(b.getAttribute("data-ans")); }); });
  }
  function answer(choice){
    var g=game; if(g.answered) return; g.answered=true;
    var q=g.pool[g.i]; var correct=(choice===q.ans); var gain=0;
    if(correct){ g.combo++; g.maxcombo=Math.max(g.maxcombo,g.combo); gain=10+Math.min(g.combo,10); g.score+=gain; }
    else { g.combo=0; g.wrong.push(q); var w=store.get("wrong",[]); if(w.indexOf(q.id)<0){ w.push(q.id); store.set("wrong",w); } }
    var src=(q.sources||[]).filter(Boolean).map(fmtSrc).join(", ");
    var h='<div class="reveal '+(correct?"ok":"no")+'">';
    h+='<div class="v">'+(correct?"정답! ":"오답 ")+'· 옳은 답은 「'+q.ans+'」</div>';
    if(q.ans==="X"){ h+='<div>이 지문은 <b>틀린 지문(함정)</b>입니다.</div>'; if(q.truth) h+='<div class="truth"><b>옳은 법리:</b> '+esc(q.truth)+'</div>'; }
    else { h+='<div>이 지문은 <b>옳은 지문</b>입니다.</div>'; }
    h+='<div class="truth"><b>조문:</b> '+esc(q.art)+' &nbsp;<b>근거:</b> '+linkifyRef(q.ref||"-")+(src?' &nbsp;<b>출처:</b> '+esc(src):'')+'</div></div>';
    h+='<div class="bar"><span>점수 +'+gain+'</span><button class="next" id="next">'+(g.i+1>=g.pool.length?"결과 보기":"다음 →")+'</button></div>';
    el("#rv").innerHTML=h;
    el("#content").querySelectorAll("[data-ans]").forEach(function(b){ b.disabled=true; b.style.opacity=.55; });
    var cb=el("#content").querySelector('[data-ans="'+q.ans+'"]'); if(cb){ cb.style.opacity=1; cb.style.outline="3px solid "+(q.ans==="O"?"#5dcaa5":"#f0a0a0"); }
    el("#next").addEventListener("click",function(){ g.i++; drawGame(el("#content")); window.scrollTo(0,0); });
  }
  function drawEnd(c){
    var g=game; var n=g.pool.length; var right=n-g.wrong.length; var pct=Math.round(right/n*100);
    var nick=store.get("nick","");
    var h='<div class="cbt-wrap"><div class="q-card" style="text-align:center">';
    h+='<h2 style="margin:0 0 6px">결과</h2>';
    h+='<div style="font-size:42px;font-weight:800;color:var(--brand-d)">'+g.score+'<span style="font-size:18px">점</span></div>';
    h+='<p style="color:var(--ink2)">'+n+'문항 중 <b>'+right+'</b>개 정답 ('+pct+'%) · 최고 콤보 🔥'+g.maxcombo+'</p>';
    h+='<div style="display:flex;gap:8px;justify-content:center;align-items:center;margin:10px 0">'
      +'<input id="nick" placeholder="닉네임" value="'+esc(nick)+'" maxlength="12" style="padding:9px 11px;border:1px solid var(--line);border-radius:8px;font-size:14px">'
      +'<button class="btn-play" id="reg">🏆 고득점 등록</button></div>';
    h+='<div id="regmsg" class="ref" style="min-height:16px"></div>';
    h+='<div style="display:flex;gap:10px;justify-content:center;margin-top:6px"><button class="btn-play" id="again" style="background:var(--brand-l)">다시 풀기</button><a class="opt" href="#/sub/'+encodeURIComponent(CURSUB||DEFAULT_SUB)+'" style="display:inline-flex;align-items:center">위키로</a></div>';
    h+='<div style="text-align:left;margin-top:18px"><div class="sect-h"><b>🏆 고득점</b></div><div id="board">'+boardHTML(10)+'</div></div>';
    if(g.wrong.length){
      h+='<div style="text-align:left;margin-top:18px"><div class="sect-h"><b>틀린 문항 ('+g.wrong.length+') — 오답노트 저장됨</b></div>';
      g.wrong.forEach(function(q){
        h+='<div class="card"><div class="row"><span class="'+(q.ans==="X"?"tag-x":"tag-o")+'">'+q.ans+'</span><div><div class="stmt" style="font-size:13.5px">'+esc(q.stmt)+'</div>'
          +(q.ans==="X"&&q.truth?'<div class="truth" style="border:none;padding:6px 0 0"><b>옳은 법리:</b> '+esc(q.truth)+'</div>':'')
          +'<div class="meta"><span class="chip">'+esc(q.art)+'</span>'+srcChips(q.sources,3)+'<span class="ref">'+esc(q.ref||"")+'</span></div></div></div></div>';
      });
      h+='</div>';
    }
    h+='</div></div>';
    c.innerHTML=h;
    var done=false;
    el("#reg").addEventListener("click",function(){
      if(done) return;
      var name=(el("#nick").value||"").trim()||"익명"; store.set("nick",name);
      addScore({name:name,score:g.score,pct:pct,scope:g.scope||"전체",date:new Date().toISOString().slice(2,10).replace(/-/g,".")});
      el("#board").innerHTML=boardHTML(10); el("#regmsg").textContent="등록 완료! (Supabase 연결 시 전체 랭킹에 반영)"; done=true;
    });
    el("#again").addEventListener("click",function(){ game=null; location.hash="#/cbt?sub="+encodeURIComponent(CURSUB||DEFAULT_SUB); render(); });
  }

  function renderBoard(c){
    var posts=store.get("posts",null);
    if(!posts){ posts=[{t:"법원직 9급 민소 OX, 이렇게 돌리니 회독이 빨라요",a:"합격기원",d:"2026-06-10",cat:"후기"},
                       {t:"제216조 기판력 객관적 범위 — 상계 항변 정리 공유",a:"민소러",d:"2026-06-08",cat:"자료"}]; store.set("posts",posts); }
    var h='<div class="wrap single"><div class="main">';
    h+='<div class="sect-h"><b>자유게시판</b><span>수험 후기·자료·질문</span></div><div class="panel">';
    posts.forEach(function(p){ h+='<div class="li"><span class="cat">'+esc(p.cat||"일반")+'</span><span class="ti">'+esc(p.t)+'</span><span class="mt">'+esc(p.a)+' · '+esc(p.d)+'</span></div>'; });
    h+='</div><div class="card" style="margin-top:14px"><b style="display:block;margin-bottom:8px">새 글 쓰기</b>'
      +'<input id="pt" placeholder="제목" style="width:100%;padding:9px;border:1px solid var(--line);border-radius:8px;margin-bottom:8px">'
      +'<input id="pa" placeholder="닉네임" style="width:100%;padding:9px;border:1px solid var(--line);border-radius:8px;margin-bottom:8px">'
      +'<button class="btn-play" id="post">등록</button> <span class="ref">데모: 이 브라우저에 저장. 배포 시 Supabase 연동.</span></div></div></div>';
    c.innerHTML=h;
    el("#post").addEventListener("click",function(){
      var t=el("#pt").value.trim(); if(!t) return;
      var a=el("#pa").value.trim()||"익명"; var d=new Date().toISOString().slice(0,10);
      posts.unshift({t:t,a:a,d:d,cat:"일반"}); store.set("posts",posts); renderBoard(c);
    });
  }
  function renderNews(c){
    var items=[{t:"법원공무원 채용시험 일정·과목 안내 (예시)",s:"법원직.com",d:"2026"},
               {t:"민사소송법 개정 시행 (2025-07-12)",s:"국가법령정보",d:"2025-07"},
               {t:"형사소송법 조문 완비 + 민소 통합본 v022",s:"법원직.com",d:"2026-06"}];
    var h='<div class="wrap single"><div class="main"><div class="sect-h"><b>뉴스</b><span>공지·법령개정·업데이트 (예시)</span></div><div class="panel">';
    items.forEach(function(p){ h+='<div class="li"><span class="ti">'+esc(p.t)+'</span><span class="mt">'+esc(p.s)+' · '+esc(p.d)+'</span></div>'; });
    h+='</div></div></div>'; c.innerHTML=h;
  }

  function bindSearch(){
    var q=el("#q");
    q.addEventListener("input",function(){
      var v=q.value.trim(); var toc=document.querySelector(".toc"); if(!toc) return;
      toc.querySelectorAll(".pbody").forEach(function(b){ b.classList.remove("hide"); });
      toc.querySelectorAll(".arts a").forEach(function(a){
        var hit=!v || a.textContent.indexOf(v)>=0 || (a.getAttribute("title")||"").indexOf(v)>=0;
        a.style.display=hit?"":"none";
      });
    });
    el("#search").addEventListener("submit",function(e){ e.preventDefault(); });
  }
  function bindModal(){
    var m=el("#modal");
    document.querySelectorAll("[data-login]").forEach(function(b){ b.addEventListener("click",function(){ m.classList.add("on"); }); });
    m.addEventListener("click",function(e){ if(e.target===m||e.target.hasAttribute("data-close")) m.classList.remove("on"); });
    m.querySelectorAll("[data-oauth]").forEach(function(b){ b.addEventListener("click",function(){
      var cfg=window.SUPABASE_CONFIG||{};
      if(cfg.url&&cfg.anonKey&&window.supabase){ var sb=window.supabase.createClient(cfg.url,cfg.anonKey); sb.auth.signInWithOAuth({provider:b.getAttribute("data-oauth")}); }
      else { alert("로그인은 Supabase 연결 후 활성화됩니다 (config.js).\n현재는 데모 모드입니다."); m.classList.remove("on"); }
    }); });
  }

  function render(){
    var r=route(); renderNav(r);
    var c=el("#content");
    if(r.view==="home"){ location.hash="#/sub/"+encodeURIComponent(DEFAULT_SUB); return; }
    if(r.view==="sub"){ if(REG[r.sub]){ use(r.sub); if(r.art) renderArticle(c,r); else renderSubjectHome(c); } else renderPlaceholder(c,r.sub); }
    else if(r.view==="cbt"){ renderCBT(c,r); }
    else if(r.view==="board") renderBoard(c);
    else if(r.view==="news") renderNews(c);
    window.scrollTo(0,0);
  }
  window.addEventListener("hashchange",function(){ if(route().view!=="cbt") game=null; render(); });
  window.addEventListener("scroll",function(){ var t=el("#totop"); if(t) t.classList.toggle("on",window.scrollY>400); });

  function boot(){
    var t=el("#totop"); if(t) t.addEventListener("click",function(){ window.scrollTo({top:0,behavior:"smooth"}); });
    bindSearch(); bindModal();
    if(!location.hash) location.hash="#/sub/"+encodeURIComponent(DEFAULT_SUB);
    render();
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot); else boot();
})();
