(function () {
  'use strict';
  const T = window.Tools, $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  function el(n, a, t) { const e = document.createElementNS(NS, n); for (const k in a) if (a[k] != null) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; }

  /* ネットワーク構成（親をたどると経路になる） */
  const NODES = {
    router: { name: 'ルータ', ip: '192.168.1.1', parent: null, x: 330, y: 40, kind: 'net' },
    A: { name: 'ハブA', ip: '192.168.1.11', parent: 'router', x: 170, y: 120, kind: 'net' },
    D: { name: 'ハブD', ip: '192.168.1.41', parent: 'router', x: 490, y: 120, kind: 'net' },
    B: { name: 'ハブB', ip: '192.168.1.21', parent: 'A', x: 170, y: 205, kind: 'net' },
    E: { name: 'ハブE', ip: '192.168.1.51', parent: 'D', x: 490, y: 205, kind: 'net' },
    C: { name: 'ハブC', ip: '192.168.1.31', parent: 'B', x: 250, y: 290, kind: 'net' },
    pc1: { name: '視聴覚室PC', ip: '192.168.1.71', parent: 'B', x: 80, y: 290, kind: 'host' },
    AP: { name: 'アクセスポイント', ip: '192.168.1.61', parent: 'E', x: 420, y: 290, kind: 'net' },
    F: { name: 'ハブF', ip: '192.168.1.101', parent: 'E', x: 580, y: 290, kind: 'net' },
    tab1: { name: '1年1組タブレット', ip: '192.168.1.91', parent: 'AP', x: 420, y: 360, kind: 'host' }
  };
  const NETDEVS = ['router', 'A', 'B', 'C', 'D', 'E', 'AP', 'F'];
  const TARGETS = ['router', 'A', 'B', 'C', 'D', 'E', 'AP', 'F'];

  function pathTo(id) { const p = []; let c = id; while (c) { p.push(c); c = NODES[c].parent; } return p; }
  /** from から to へ届くか（broken が故障中の機器） */
  function reach(from, to, broken) {
    const pf = pathTo(from), pt = pathTo(to);
    // 共通の祖先を探す
    let common = null;
    for (const x of pf) if (pt.indexOf(x) >= 0) { common = x; break; }
    if (!common) return false;
    const route = pf.slice(0, pf.indexOf(common) + 1).concat(pt.slice(0, pt.indexOf(common)).reverse());
    return route.indexOf(broken) < 0;
  }

  let broken = 'A', from = 'pc1', results = {}, answered = false;

  /* ---------- 図 ---------- */
  function drawTopo() {
    const W = 680, H = 410;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: 'img', 'aria-label': 'ネットワーク構成図' });
    svg.appendChild(el('text', { x: 330, y: 14, 'font-size': 11, fill: '#4a4f57', 'text-anchor': 'middle' }, 'インターネット'));
    svg.appendChild(el('line', { x1: 330, y1: 18, x2: 330, y2: 26, class: 'link' }));
    Object.keys(NODES).forEach(id => {
      const n = NODES[id];
      if (!n.parent) return;
      const p = NODES[n.parent];
      const dead = (broken === id || broken === n.parent);
      svg.appendChild(el('line', { x1: p.x, y1: p.y + 16, x2: n.x, y2: n.y - 16,
        class: 'link' + (answered && dead ? ' dead' : '') }));
    });
    const suspects = computeSuspects();
    Object.keys(NODES).forEach(id => {
      const n = NODES[id];
      let cls = 'dev';
      if (id === from) cls += ' here';
      else if (results[from] && results[from][id] === true) cls += ' ok';
      else if (results[from] && results[from][id] === false) cls += ' ng';
      if (!answered && suspects.indexOf(id) >= 0) cls += ' suspect';
      if (answered && id === broken) cls += ' broken';
      const g = el('g', {});
      const w = n.kind === 'host' ? 118 : 96;
      g.appendChild(el('rect', { x: n.x - w / 2, y: n.y - 16, width: w, height: 34, rx: 3, class: cls, 'data-id': id }));
      g.appendChild(el('text', { x: n.x, y: n.y - 3, class: 'dname' }, n.name));
      g.appendChild(el('text', { x: n.x, y: n.y + 11, class: 'dip' }, n.ip));
      if (TARGETS.indexOf(id) >= 0) {
        g.style.cursor = 'pointer';
        g.addEventListener('click', () => ping(id));
      }
      svg.appendChild(g);
    });
    const box = $('topoBox'); box.innerHTML = ''; box.appendChild(svg);
  }

  /* ---------- 疎通確認 ---------- */
  function ping(to) {
    if (!results[from]) results[from] = {};
    const ok = reach(from, to, broken);
    results[from][to] = ok;
    const m = $('pingMsg');
    m.className = 'note ' + (ok ? 'ok' : 'ng');
    m.innerHTML = NODES[from].name + ' から <strong>' + NODES[to].name + '（' + NODES[to].ip + '）</strong>へ：' +
      (ok ? '<strong>パケットが届きました（○）</strong>' : '<strong>パケットが届きません（×）</strong>');
    drawAll();
  }
  function drawTable() {
    const rows = [];
    ['pc1', 'tab1'].forEach(f => {
      if (!results[f]) return;
      TARGETS.forEach(t => {
        if (results[f][t] === undefined) return;
        rows.push({ f, t, ok: results[f][t] });
      });
    });
    if (!rows.length) { $('pingTable').innerHTML = '<tbody><tr><td>まだ調べていません</td></tr></tbody>'; return; }
    $('pingTable').innerHTML = '<thead><tr><th>調べた場所</th><th>送信先</th><th>IPアドレス</th><th>結果</th></tr></thead><tbody>' +
      rows.map(r => '<tr><td>' + NODES[r.f].name + '</td><td>' + NODES[r.t].name + '</td><td>' + NODES[r.t].ip +
        '</td><td class="' + (r.ok ? 'ok' : 'ng') + '">' + (r.ok ? '○ 届く' : '× 届かない') + '</td></tr>').join('') + '</tbody>';
  }

  /* ---------- 候補の絞り込み ---------- */
  function computeSuspects() {
    const obs = [];
    Object.keys(results).forEach(f => Object.keys(results[f]).forEach(t => obs.push([f, t, results[f][t]])));
    if (!obs.length) return [];
    return NETDEVS.filter(cand => obs.every(([f, t, ok]) => reach(f, t, cand) === ok));
  }
  function drawSuspects() {
    const s = computeSuspects();
    const n = $('suspectNote');
    const obsCount = Object.keys(results).reduce((a, f) => a + Object.keys(results[f]).length, 0);
    if (!obsCount) {
      n.className = 'note info';
      n.textContent = 'まだ疎通確認をしていません。STEP 2 で機器をクリックしてください。';
      $('suspectList').innerHTML = '';
    } else if (s.length === 0) {
      n.className = 'note ng';
      n.innerHTML = '1台の故障では説明できない結果です。記録を消してやり直してください。';
      $('suspectList').innerHTML = '';
    } else if (s.length === 1) {
      n.className = 'note ok';
      n.innerHTML = '<strong>1台に絞れました。</strong>これまでの ' + obsCount + ' 回の疎通確認から、故障しているのは ' +
        '<strong>' + NODES[s[0]].name + '</strong> だと特定できます。';
      $('suspectList').innerHTML = '<span class="s">' + NODES[s[0]].name + '</span>';
    } else {
      n.className = 'note warn';
      n.innerHTML = '候補は <strong>' + s.length + ' 台</strong>です。まだ特定できません。' +
        '<strong>別の場所（' + (from === 'pc1' ? '1年1組のタブレット' : '視聴覚室のPC') + '）から調べる</strong>と、通る経路が変わって絞り込めます。';
      $('suspectList').innerHTML = s.map(x => '<span class="s">' + NODES[x].name + '</span>').join('');
    }
    // 解答ボタン
    const box = $('answerBox');
    box.className = 'choice4'; box.innerHTML = '';
    NETDEVS.forEach(id => {
      const b = document.createElement('button');
      b.className = 'btn'; b.textContent = NODES[id].name; b.dataset.id = id;
      b.style.textAlign = 'center';
      b.addEventListener('click', () => answerCase(id));
      box.appendChild(b);
    });
  }
  function answerCase(id) {
    answered = true;
    const fb = $('answerFb'); fb.hidden = false;
    const ok = id === broken;
    fb.className = 'note ' + (ok ? 'ok' : 'ng');
    fb.innerHTML = ok
      ? '<strong>正解です。</strong>故障していたのは ' + NODES[broken].name + ' でした。図で赤く表示しています。'
      : '<strong>ちがいます。</strong>正解は ' + NODES[broken].name + '。もう一度、届く機器と届かない機器の境目を確かめてみましょう。';
    $('answerBox').classList.add('locked');
    [...$('answerBox').children].forEach(b => {
      if (b.dataset.id === broken) b.classList.add('correct');
      else if (b.dataset.id === id) b.classList.add('wrong');
    });
    drawTopo();
  }
  function newCase() {
    broken = NETDEVS[Math.floor(Math.random() * NETDEVS.length)];
    results = {}; answered = false; from = 'pc1';
    $('answerFb').hidden = true;
    $('pingMsg').className = 'note info';
    $('pingMsg').textContent = '新しい故障で出題しました。図の機器をクリックして調べてください。';
    document.querySelectorAll('[data-from]').forEach(b => b.setAttribute('aria-pressed', b.dataset.from === from));
    drawAll();
  }

  /* ---------- STEP5 クイズ ---------- */
  const QUIZ = [
    { t: 'スイッチングハブが1台故障すると、どうなるか。',
      choices: ['そのハブより先につながる機器すべてに届かなくなる', 'ネットワーク全体が止まる',
                '通信が遅くなるだけで届きはする', '無線だけが使えなくなる'],
      a: 'そのハブより先につながる機器すべてに届かなくなる',
      why: 'ハブは通信の通り道です。壊れると、その先に枝分かれしている機器すべてが切り離されます。' },
    { t: '故障の候補が2台に絞れたとき、次にすべきことは何か。',
      choices: ['別の場所から疎通確認をする', '同じ場所からもう一度同じ機器を調べる',
                'すべての機器を再起動する', 'あきらめて機器を交換する'],
      a: '別の場所から疎通確認をする',
      why: '場所を変えると通る経路が変わるので、新しい情報が得られます。同じ場所から同じ機器を調べても結果は変わりません。' },
    { t: 'ルータが故障したとき、いちばん影響が大きいのはどれか。',
      choices: ['インターネットや他のネットワークへ出られなくなる', '同じハブにつながる機器どうしの通信ができなくなる',
                '無線LANだけが使えなくなる', 'IPアドレスの表記が変わる'],
      a: 'インターネットや他のネットワークへ出られなくなる',
      why: 'ルータはネットワークどうしの出入り口です。同じハブ内の通信は続けられますが、外には出られません。' },
    { t: '疎通確認で「届く」機器が1つでもあれば、何が言えるか。',
      choices: ['自分からその機器までの経路上の機器はすべて動いている', '故障は起きていない',
                'その機器が故障している', 'ネットワーク全体が正常である'],
      a: '自分からその機器までの経路上の機器はすべて動いている',
      why: 'パケットが通れたということは、その道すじの機器がすべて生きているということです。ここから候補を減らせます。' },
    { t: 'この種の問題で「1台だけ故障している」という条件が書かれるのはなぜか。',
      choices: ['複数の故障を考えると候補が絞れなくなるから', '1台しか壊れないから',
                '計算が簡単になるから', 'ルータは壊れないから'],
      a: '複数の故障を考えると候補が絞れなくなるから',
      why: '2台以上が同時に壊れている可能性を認めると、組み合わせが増えて特定できません。前提条件を必ず確認しましょう。' }
  ];
  let qList = [], qi = 0, qScore = 0;
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  function startQuiz() { qList = shuffle(QUIZ); qi = 0; qScore = 0; renderQ(); }
  function renderQ() {
    if (qi >= qList.length) {
      $('qText').textContent = qScore + ' / ' + qList.length + ' 問正解';
      $('qChoices').innerHTML = ''; $('qFb').hidden = true; $('qNext').disabled = true;
      $('qProgress').textContent = qList.length + ' / ' + qList.length; return;
    }
    const it = qList[qi];
    $('qProgress').textContent = (qi + 1) + ' / ' + qList.length;
    $('qScore').textContent = qScore;
    $('qText').textContent = it.t;
    const box = $('qChoices'); box.className = 'choice4'; box.innerHTML = '';
    shuffle(it.choices).forEach(c => {
      const b = document.createElement('button');
      b.className = 'btn'; b.textContent = c; b.dataset.c = c;
      b.addEventListener('click', () => answerQ(c));
      box.appendChild(b);
    });
    $('qFb').hidden = true; $('qNext').disabled = true;
    $('qNext').textContent = (qi === qList.length - 1) ? '結果を見る' : '次の問題';
  }
  function answerQ(c) {
    const it = qList[qi], ok = c === it.a, box = $('qChoices');
    box.classList.add('locked');
    [...box.children].forEach(b => {
      if (b.dataset.c === it.a) b.classList.add('correct');
      else if (b.dataset.c === c) b.classList.add('wrong');
    });
    if (ok) qScore++;
    const fb = $('qFb');
    fb.className = 'note ' + (ok ? 'ok' : 'ng');
    fb.innerHTML = (ok ? '正解。' : '正解は「<strong>' + it.a + '</strong>」。') + it.why;
    fb.hidden = false;
    $('qScore').textContent = qScore; $('qNext').disabled = false;
  }

  function drawAll() { drawTopo(); drawTable(); drawSuspects(); }

  /* 本文の問題 */
  function drawBook() {
    if (!document.getElementById('bookBox')) return;
    window.Quiz.choice('bookBox', 'bookNote', [{"k": "ア・イ", "q": "視聴覚室からの疎通結果から、故障の可能性がある機器は（2つのうちの1つ）。", "ch": ["Aのスイッチングハブ", "Bのスイッチングハブ", "Cのスイッチングハブ", "Dのスイッチングハブ", "Eのスイッチングハブ", "Fのスイッチングハブ", "ルータ", "この情報では特定できない"], "a": "2|0", "why": "視聴覚室からは 192.168.1.61 と 192.168.1.101 には届き、それ以外には届きません。届く相手と届かない相手を分ける位置にある機器が候補になります。"}, {"k": "ウ", "q": "1年1組のタブレットから、どこにパケットが届けば故障箇所を特定できるか。", "ch": ["192.168.1.11", "192.168.1.21", "192.168.1.31", "192.168.1.61", "192.168.1.101"], "a": 0, "why": "2つの候補のうち、片方が故障のときだけ届く相手を選びます。届けば一方、届かなければもう一方と切り分けられます。"}], "本文の答えは【ア】②　【イ】⓪（順不同）　【ウ】⓪ です。STEP 2・3 の考え方がそのまま使えます。");
  }

  function init() {
    document.querySelectorAll('[data-from]').forEach(b => b.addEventListener('click', () => {
      from = b.dataset.from;
      document.querySelectorAll('[data-from]').forEach(x => x.setAttribute('aria-pressed', x.dataset.from === from));
      $('pingMsg').className = 'note info';
      $('pingMsg').innerHTML = '<strong>' + NODES[from].name + '</strong> から調べます。図の機器をクリックしてください。';
      drawAll();
    }));
    $('clearPing').addEventListener('click', () => { results = {}; answered = false; $('answerFb').hidden = true; drawAll(); });
    $('newCase').addEventListener('click', newCase);
    $('reveal').addEventListener('click', () => { answered = true; 
      const fb = $('answerFb'); fb.hidden = false; fb.className = 'note info';
      fb.innerHTML = '故障していたのは <strong>' + NODES[broken].name + '</strong> でした。'; drawTopo(); });
    $('qNext').addEventListener('click', () => { qi++; renderQ(); });
    $('qReset').addEventListener('click', startQuiz);
    window.Terms.glossary($('glossBox'), ['ルータ', 'スイッチングハブ', 'アクセスポイント', 'LAN', 'IPアドレス', 'パケット', 'プロトコル']);
    document.querySelectorAll('[data-from]').forEach(b => b.setAttribute('aria-pressed', b.dataset.from === from));
    drawAll(); startQuiz();
    drawBook();
    window.Terms.attach();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
