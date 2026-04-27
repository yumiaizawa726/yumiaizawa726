from IPython.display import HTML, display
import json

UI_HTML = '''
<style>
.jap-wrap *{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}
.jap-wrap{padding:12px 0}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:1rem}
.sc{background:#f5f5f3;border-radius:8px;padding:12px 14px}
.sl{font-size:11px;color:#888;margin-bottom:4px}
.sv{font-size:24px;font-weight:500}
.sv.g{color:#1D9E75}.sv.m{color:#BA7517}.sv.b{color:#A32D2D}
.bw{height:4px;background:#e5e5e3;border-radius:2px;margin-top:5px}
.bf{height:4px;border-radius:2px}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:1rem}
.chip{font-size:11px;padding:3px 10px;border-radius:99px}
.stitle{font-size:11px;font-weight:500;color:#888;letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px}
.scard{background:#fff;border:0.5px solid #e5e5e3;border-radius:10px;padding:10px 12px;margin-bottom:6px}
.stxt{font-size:14px;color:#222;margin-bottom:8px;line-height:1.6}
.tags{display:flex;flex-wrap:wrap;gap:4px}
.tag{font-size:11px;padding:2px 9px;border-radius:99px}
.ts{background:#E6F1FB;color:#0C447C}
.tp{background:#EAF3DE;color:#3B6D11}
.to{background:#FAEEDA;color:#633806}
.tc{background:#f5f5f3;color:#666}
.tt{background:#EEEDFE;color:#3C3489}
.tn{background:#FCEBEB;color:#791F1F}
.arow{display:flex;align-items:flex-start;gap:8px;padding:8px 12px;border-radius:7px;margin-bottom:5px;border:0.5px solid #e5e5e3}
.ab{font-size:11px;font-weight:500;padding:2px 8px;border-radius:99px;white-space:nowrap;flex-shrink:0;margin-top:1px}
.aw{background:#FAEEDA;color:#633806}.ae{background:#FCEBEB;color:#791F1F}.aok{background:#EAF3DE;color:#3B6D11}.ax{background:#EEEDFE;color:#3C3489}
.atxt{font-size:12px;color:#666;line-height:1.6}
.pw{flex:1;height:5px;background:#f0f0ee;border-radius:3px}
.pb{height:5px;border-radius:3px;background:#EF9F27}
.sec{margin-bottom:1.1rem}
</style>
<div class="jap-wrap" id="jap-UID"></div>
<script>
(function(){
  var r = RESULT_JSON;
  var el = document.getElementById("jap-UID");
  function sc(v){return v>=80?"g":v>=60?"m":"b"}
  function bc(v){return v>=80?"#1D9E75":v>=60?"#BA7517":"#A32D2D"}
  var s = r.score;
  var html = "<div class='sec'><div class='stitle'>総合スコア</div><div class='sg'>";
  [{"label":"総合スコア","key":"総合スコア"},{"label":"主語明確性","key":"主語明確性"},{"label":"論理整合性","key":"論理整合性"},{"label":"ポエム減点","key":"ポエム減点","inv":true}].forEach(function(m){
    var v=s[m.key],cls=m.inv?(v===0?"g":"b"):sc(v),col=m.inv?(v===0?"#1D9E75":"#A32D2D"):bc(v),pct=m.inv?Math.min(100,v*3):v;
    html+="<div class='sc'><div class='sl'>"+m.label+"</div><div class='sv "+cls+"'>"+v+"</div><div class='bw'><div class='bf' style='width:"+pct+"%;background:"+col+"'></div></div></div>";
  });
  html+="</div><div class='chips'>";
  var p=s["問題数"];
  [{"k":"主語"},{"k":"論理"},{"k":"表現"},{"k":"ポエム"}].forEach(function(c){
    var ok=p[c.k]===0,bg=ok?"background:#EAF3DE;color:#3B6D11":"background:#FCEBEB;color:#791F1F";
    html+="<span class='chip' style='"+bg+"'>"+c.k+": "+p[c.k]+"件</span>";
  });
  html+="</div></div>";

  html+="<div class='sec'><div class='stitle'>構文解析</div>";
  r.structure.forEach(function(s){
    var tags="";
    if(s.subject){
      tags+="<span class='tag ts'>主語 "+s.subject+"</span>";
      if(s.subject_type) tags+="<span class='tag tt'>"+s.subject_type+"</span>";
      if(s.subject_confidence) tags+="<span class='tag tc'>確信度 "+Math.round(s.subject_confidence*100)+"%</span>";
    } else { tags+="<span class='tag tn'>主語なし</span>"; }
    if(s.predicate) tags+="<span class='tag tp'>述語 "+s.predicate+"</span>";
    if(s.object) tags+="<span class='tag to'>目的語 "+s.object+"</span>";
    html+="<div class='scard'><div class='stxt'>"+s.sentence+"</div><div class='tags'>"+tags+"</div></div>";
  });
  html+="</div>";

  html+="<div class='sec'><div class='stitle'>論理整合性</div>";
  if(r.coherence_alerts.length===0){
    html+="<div class='arow'><span class='ab aok'>問題なし</span><span class='atxt'>論理飛躍は検出されませんでした</span></div>";
  } else {
    r.coherence_alerts.forEach(function(a){
      var cls=a.alert==="トピックジャンプ"?"ae":"aw";
      html+="<div class='arow'><span class='ab "+cls+"'>"+a.alert+"</span><span class='atxt'>"+a.pair[0]+" → "+a.pair[1]+"<br>類似度: "+a.similarity+"</span></div>";
    });
  }
  html+="</div>";

  html+="<div class='sec'><div class='stitle'>表現の問題</div>";
  if(!r.weak_claims || r.weak_claims.length===0){
    html+="<div class='arow'><span class='ab aok'>問題なし</span><span class='atxt'>抽象表現の過多は検出されませんでした</span></div>";
  } else {
    r.weak_claims.forEach(function(a){
      html+="<div class='arow'><span class='ab ax'>"+a.alert+"</span><span class='atxt'>"+a.sentence+"<br><span style='color:#999'>"+a.reason+"</span></span></div>";
    });
  }
  html+="</div>";

  html+="<div class='sec'><div class='stitle'>ポエム密度</div>";
  if(!r.poetic){
    html+="<div class='arow'><span class='ab aok'>対象外</span><span class='atxt'>短文のため判定をスキップ</span></div>";
  } else {
    var pct=Math.min(100,Math.round(r.poetic.ratio*100));
    var apct=Math.min(100,Math.round((r.poetic.abstract_density||0)*100));
    var badge=r.poetic.alert?"<span class='ab aw' style='margin-left:8px'>"+r.poetic.alert+"</span>":"";
    html+="<div class='arow' style='flex-direction:column;gap:6px'>";
    html+="<div style='display:flex;align-items:center;gap:8px;width:100%'><span class='atxt' style='white-space:nowrap;width:80px'>形容詞率 "+r.poetic.ratio+"</span><div class='pw'><div class='pb' style='width:"+pct+"%'></div></div>"+badge+"</div>";
    html+="<div style='display:flex;align-items:center;gap:8px;width:100%'><span class='atxt' style='white-space:nowrap;width:80px'>抽象語率 "+(r.poetic.abstract_density||0)+"</span><div class='pw'><div class='pb' style='width:"+apct+"%;background:#9B59B6'></div></div></div>";
    html+="</div>";
  }
  html+="</div>";
  el.innerHTML=html;
})();
</script>
'''

_uid_counter = [0]

def display_analysis(text):
    result = full_analysis(text)
    uid = _uid_counter[0]
    _uid_counter[0] += 1
    result_json = json.dumps(result, ensure_ascii=False)
    html = UI_HTML.replace("RESULT_JSON", result_json).replace("UID", str(uid))
    display(HTML(html))
