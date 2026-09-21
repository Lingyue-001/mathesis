import {test} from 'node:test';
import assert from 'node:assert/strict';
import {sourceRows, fragments} from '../../tools/parser_inspector/source_annotation.mjs';
import {layoutProcedureModel} from '../../tools/parser_inspector/procedure_model.mjs';

test('rows wrap at punctuation and preserve every original code point', () => {
  const text = '推天正術，置入蔀年減一，以章月乘之，滿章法得一，名為積月，不滿為閏餘，十二以上，其歲有閏。';
  const chars = Array.from(text), rows = sourceRows(chars, chars.map(() => 26), 420);
  assert.ok(rows.length > 1);
  assert.equal(rows.map(r => r.text).join(''), text);
  assert.equal(rows[0].row_start, 0);
  assert.equal(rows.at(-1).row_end, chars.length);
  rows.forEach((row, i) => {
    assert.equal(row.text, chars.slice(row.row_start, row.row_end).join(''));
    assert.ok((row.row_end - row.row_start) * 26 <= 420);
    if (i) assert.equal(row.row_start, rows[i-1].row_end);
  });
});

test('cross-row fragments retain canonical identity and original span', () => {
  const rows = sourceRows(Array.from('以章月乘章月'), Array(6).fill(30), 90);
  const object = {id:'multiply', span:[0,6]};
  assert.deepEqual(rows.flatMap(row => fragments([object],row)).map(r => [r.id,r.span,r.fragment]),
                   [['multiply',[0,6],[0,3]],['multiply',[0,6],[3,6]]]);
});

test('layout does not depend on gloss width and handles astral Unicode', () => {
  const chars=Array.from('甲𠀀乙，丙丁。');
  const widths=chars.map(()=>24);
  const rows=sourceRows(chars,widths,110);
  assert.equal(rows.map(r=>r.text).join(''),'甲𠀀乙，丙丁。');
  assert.deepEqual(rows,sourceRows(chars,widths,110));
});

test('procedure layout retains disconnected nodes and cycles without guessing edges',()=>{
  const model={nodes:[{id:'a',type:'operation'},{id:'b',type:'operation'},{id:'c',type:'literal'}],
    edges:[{from:'a',to:'b'},{from:'b',to:'a'}]};
  const original=JSON.stringify(model),layout=layoutProcedureModel(model);
  assert.equal(layout.positions.size,3);
  assert.deepEqual(layout.cyclic,['a','b']);
  assert.equal(layout.positions.get('c').width,70);
  assert.equal(JSON.stringify(model),original);
  assert.deepEqual(layoutProcedureModel(model),layout);
});
