(function(){
  var input=document.getElementById('hookInput');
  var results=document.getElementById('results');
  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;');}
  function analyze(){
    var raw=input.value.trim();
    if(!raw){results.className='results show';results.innerHTML='<div class="rrow fail"><div class="ic">✕</div><div>先输入一句候选钩子再体检。</div></div>';return;}
    var s=raw.replace(/\s+/g,'');
    var len=s.length;
    var rows=[]; var score=0,total=0;
    function add(cls,ok,html){rows.push({cls:cls,html:html});total++;if(ok==='pass')score++;else if(ok==='mid')score+=0.5;}
    // 1 throat-clearing
    var throat=/^(大家好|您好|哈喽|hello|hi|欢迎来到|欢迎回来|我是|本期视频|今天我们|今天来聊|今天给大家)/i.test(raw);
    if(throat)add('fail','fail','<b>零清嗓子：不合格。</b>开头是问候 / 自我介绍 / 「今天我们……」——承诺之前的东西全部剪掉，从最强的那句开始。');
    else add('pass','pass','<b>零清嗓子：过。</b>没有问候、自我介绍或「今天我们来聊聊」式开场。');
    // 2 length
    if(len<=15)add('pass','pass','<b>长度：'+len+' 字，过。</b>在抖音实务的 ≤15 字口径内，3 秒内能说完，承诺能在第 2 秒前落地。');
    else if(len<=25)add('mid','mid','<b>长度：'+len+' 字，偏长。</b>超出 ≤15 字的严口径（部分中文手册放宽到 25 字）。对着计时器读一遍，承诺没在第 2 秒前说完就删词。');
    else add('fail','fail','<b>长度：'+len+' 字，不合格。</b>3 秒说不完，承诺落地时人已经划走了。压到一口气能说完的一句。');
    // 3 number / specific artifact
    var hasNum=/[0-9０-９]/.test(raw)||/[二三四五六七八九十百千万两]/.test(raw);
    if(hasNum)add('pass','pass','<b>具体性（数字）：过。</b>句中有数字——数字可核查、能想象、划定范围，也让正文承诺了一个可数的兑现。');
    else add('mid','mid','<b>具体性（数字）：无数字。</b>没有数字不必然判死，但判据 2 要求至少有一个「能画出来的名词 / 看得见的实物」。检查这句里有没有有名有姓的名词；如果只有「这个 / 秘密 / 方法」这类词，不合格。');
    // 4 vague words
    var vague=['你不会相信','不可思议','没人告诉','没人知道','震惊','惊呆','竟然是','秘密','绝密','唯一的方法','所有人都'];
    var hit=vague.filter(function(w){return raw.indexOf(w)>=0;});
    if(hit.length)add('fail','fail','<b>模糊词：命中「'+hit.join('」「')+'」。</b>这类词不给答案的类别，大脑会把钩子归档为「饵」。改法：说出答案的类别，不给答案——点名那个人、那个数、那件实物。');
    else add('pass','pass','<b>模糊词：过。</b>没有「你不会相信 / 没人告诉你 / 震惊」这类空吊胃口的词。');
    // 5 second person / identity
    var hasYou=/你|您|姐妹|同学|家长|妈妈|爸爸|老人/.test(raw);
    if(hasYou)add('pass','pass','<b>点名受众：过。</b>句中有第二人称或明确人群称呼，目标观众能对号入座。注意：「你」要配具体处境，泛泛的「你想赚钱吗」不算。');
    else add('mid','mid','<b>点名受众：未点名。</b>判据 4 要求说清这是给谁的。不是每句都必须带「你」，但要在封面或第一帧里让目标观众 1 秒内认出自己——否则这句勾的是所有人，也就是谁都不勾。');
    // 6 negation / question / gap shape
    var hasNeg=/别再|不要|别|错|不是|停止|千万别|原来不/.test(raw);
    var hasQ=/[?？]|谁|哪|为什么|怎么|吗/.test(raw);
    if(hasNeg)add('pass','pass','<b>缺口形状（否定式）：过。</b>否定 / 纠错框定同时触发认知失调与损失厌恶——观众会自查「我是不是也错了」。前提：正文数秒内给出可信的纠正，否则反噬。');
    else if(hasQ)add('pass','pass','<b>缺口形状（提问式）：过。</b>问句 / 疑问词开了一个形状明确的缺口。自查：这是观众自己已经在问的问题吗？泛问题（「想省钱吗？」）不算。');
    else add('mid','mid','<b>缺口形状：偏陈述。</b>没有问句、也没有否定 / 纠错。陈述句要当钩子，必须是大胆断言或结果前置（先给终局画面）。自查：观众看完这句，心里有没有一个「想知道」的空？');
    // 7 one promise (rough: multiple question marks / commas segments)
    var segs=raw.split(/[，,、；;]/).filter(function(x){return x.trim().length>0;});
    if(segs.length>3)add('mid','mid','<b>单一承诺：可能超载。</b>句子被切成 '+segs.length+' 段。判据 8：一个钩子只许一个承诺、一个缺口；两段以上各说一件事，注意力就被分流。');
    else add('pass','pass','<b>单一承诺：过。</b>句子聚焦在一个缺口上（'+segs.length+' 段）。最后仍要人工确认：封面、第一帧、第一个声音许的是同一个承诺，且正文里能指出兑现的时间戳。');
    var pct=Math.round(score/total*100);
    var verdict=pct>=85?'句子层基本合格——接下来过静音测试、首帧冻结和兑现时间戳。':(pct>=55?'有硬伤：先修标 ✕ 的项，再谈拍摄。':'不合格：这还不是钩子。按判据 2、3 重写——先点名一个具体名词，再开一个形状明确的缺口。');
    var html='<div class="score">体检得分 '+score+' / '+total+' · '+verdict+'</div>';
    rows.forEach(function(r){html+='<div class="rrow '+r.cls+'"><div class="ic">'+(r.cls==='pass'?'✓':(r.cls==='fail'?'✕':'!'))+'</div><div>'+r.html+'</div></div>';});
    html+='<div class="rrow mid"><div class="ic">!</div><div><b>体检器验不到的三项，人工过：</b>① 静音看前 3 秒，能否懂；② 暂停在 0:00，第一帧本身是不是钩子；③ 正文中指出承诺兑现的时间戳。三项缺一，仍判不合格。</div></div>';
    results.className='results show';results.innerHTML=html;
  }
  document.getElementById('runCheck').addEventListener('click',analyze);
  function setEx(v){input.value=v;analyze();}
  document.getElementById('ex1').addEventListener('click',function(){setEx('胡说八道的「胡」是谁，「八道」又是哪八道？');});
  document.getElementById('ex2').addEventListener('click',function(){setEx('你不会相信这个成语背后藏着的秘密');});
  document.getElementById('ex3').addEventListener('click',function(){setEx('大家好，我是小禾，今天我们来聊聊一个非常有意思的成语故事');});
  analyze();
})();
