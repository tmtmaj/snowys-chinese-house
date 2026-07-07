/* gen_md.js — regenerate A/B/E markdown + script.md from an episode's scripts.js.
   Usage: concatenate the episode's scripts.js in front of this file, then run:
     cat scripts.js gen_md.js > /tmp/combined.js
     node /tmp/combined.js "<episodeDir>" "<epNumberNNNN>" "<word>"
   scripts.js must have already defined CARDS, NARR, STYLES (globals). */

const _fs = require('fs');
const _dir  = process.argv[2];
const _epNo = process.argv[3] || '0000';
const _word = process.argv[4] || '';

const labelKR = { A: '친근한 언니/오빠', B: '유머러스한 개그맨', E: '스토리텔러/배우' };

// validate: every card has data in every style
let errs = [];
for (const c of CARDS) for (const st of ['A', 'B', 'E']) if (!NARR[st][c.id]) errs.push(st + ' ' + c.id);
console.error('CARDS', CARDS.length, '| missing:', errs.length ? errs.join(',') : 'none');
if (errs.length) { console.error('ABORT: missing narration data'); process.exit(1); }

function mdFor(style) {
  const L = ['# EP' + _epNo + ' 《' + _word + '》 Script — Style ' + style + ': ' + labelKR[style], ''];
  for (const c of CARDS) {
    const d = NARR[style][c.id];
    if (c.section) L.push('## 📖 ' + c.section, '');
    const head = c.id === 'open' ? '🎬 Opening' : c.id === 'photo' ? '🖼️ Photo' : c.badge;
    L.push('### ' + head + ' 📌 `' + c.img + '`', '');
    if (d.s) L.push('**' + d.s + '**', '');
    if (d.t) L.push(d.t, '');
    if (d.n) L.push('> 💡 ' + d.n.split('\n').join('\n> '), '');
    L.push('---', '');
  }
  return L.join('\n');
}

const files = { A: 'scripts/A_friendly-sibling.md', B: 'scripts/B_comedian.md', E: 'scripts/E_storyteller.md' };
_fs.mkdirSync(_dir + '/scripts', { recursive: true });
for (const st of ['A', 'B', 'E']) {
  _fs.writeFileSync(_dir + '/' + files[st], mdFor(st));
  console.error('wrote', files[st]);
}
_fs.writeFileSync(_dir + '/script.md', mdFor('A'));
console.error('wrote script.md (=A)');
