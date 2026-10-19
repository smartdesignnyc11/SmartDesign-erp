// The document reader on real files built here: a text PDF and a Word document read locally, a scanned PDF and a
// photo sent to the (mocked) model through the capped door, refusals and notes. node test/doctext_test.mjs
import assert from 'node:assert/strict'; import zlib from 'node:zlib';
Object.assign(process.env, {ANTHROPIC_API_KEY: 'k', SUPABASE_URL: 'https://db', SUPABASE_SERVICE_ROLE_KEY: 's', AI_MODEL_SMALL: 'claude-haiku-5-5'});
const GOOD = 'h.' + Buffer.from(JSON.stringify({session_id: 's1'})).toString('base64url') + '.sig';
const W = {calls: [], logged: [], spend: 0};
globalThis.fetch = async (url, o = {}) => {
  const u = String(url), J = (x, s = 200) => new Response(JSON.stringify(x), {status: s});
  if (u.endsWith('/auth/v1/user')) return o.headers.authorization === 'Bearer ' + GOOD ? J({id: 'u1'}) : J({}, 401);
  if (u.endsWith('/rpc/session_alive_for')) return J(true);
  if (u.includes('/rest/v1/profiles')) return J([{id: 'u1', role: 'coord', workspace_id: 'w'}]);
  if (u.endsWith('/rpc/ai_spend')) return J({firm: W.spend, user: 0});
  if (u.endsWith('/rest/v1/ai_usage')) { W.logged.push(JSON.parse(o.body)); return new Response(null, {status: 201}); }
  if (u === 'https://api.anthropic.com/v1/messages') { const b = JSON.parse(o.body); W.calls.push(b); return J({model: b.model, content: [{type: 'text', text: 'RECEIPT | Home Depot | Total $87.40'}], usage: {input_tokens: 1500, output_tokens: 40}}); }
  throw new Error('unexpected ' + u);
};
const doctext = (await import('../netlify/functions/doctext.mjs')).default;
let n = 0; const ok = (c, m) => { assert.ok(c, m); n++; };
const call = async (b, tok = GOOD) => { const r = await doctext(new Request('https://x/api/doctext', {method: 'POST', headers: tok ? {authorization: 'Bearer ' + tok} : {}, body: JSON.stringify(b)})); return [r.status, await r.json()]; };

// a one-page PDF with a text layer, written by hand
function pdf(text) {
  const stream = `BT /F1 12 Tf 72 720 Td (${text}) Tj ET`;
  const objs = ['<< /Type /Catalog /Pages 2 0 R >>', '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'];
  let out = '%PDF-1.4\n'; const offs = [];
  objs.forEach((o, i) => { offs.push(out.length); out += `${i + 1} 0 obj\n${o}\nendobj\n`; });
  const x = out.length; out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n` + offs.map(v => String(v).padStart(10, '0') + ' 00000 n \n').join('');
  return Buffer.from(out + `trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${x}\n%%EOF\n`);
}
// a minimal .docx (a zip with one document part), written by hand
function docx(text) {
  const files = {'[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
    '_rels/.rels': '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
    'word/document.xml': `<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>${text}</w:t></w:r></w:p></w:body></w:document>`};
  const crcT = []; for (let i = 0; i < 256; i++) { let c = i; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; crcT[i] = c >>> 0; }
  const crc = b => { let c = 0xFFFFFFFF; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };
  const parts = [], cen = []; let off = 0;
  for (const [name, body] of Object.entries(files)) {
    const data = Buffer.from(body), comp = zlib.deflateRawSync(data), nm = Buffer.from(name), c = crc(data);
    const h = Buffer.alloc(30); h.writeUInt32LE(0x04034b50, 0); h.writeUInt16LE(20, 4); h.writeUInt16LE(8, 8); h.writeUInt32LE(c, 14); h.writeUInt32LE(comp.length, 18); h.writeUInt32LE(data.length, 22); h.writeUInt16LE(nm.length, 26);
    parts.push(h, nm, comp);
    const e = Buffer.alloc(46); e.writeUInt32LE(0x02014b50, 0); e.writeUInt16LE(20, 4); e.writeUInt16LE(20, 6); e.writeUInt16LE(8, 10); e.writeUInt32LE(c, 16); e.writeUInt32LE(comp.length, 20); e.writeUInt32LE(data.length, 24); e.writeUInt16LE(nm.length, 28); e.writeUInt32LE(off, 42);
    cen.push(e, nm); off += 30 + nm.length + comp.length;
  }
  const cd = Buffer.concat(cen), end = Buffer.alloc(22); end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(3, 8); end.writeUInt16LE(3, 10); end.writeUInt32LE(cd.length, 12); end.writeUInt32LE(off, 16);
  return Buffer.concat([...parts, cd, end]);
}
const b64 = b => b.toString('base64');

let [s, j] = await call({data: b64(pdf('x'))}, null); ok(s === 401, 'the reader needs a signed-in member');
[s, j] = await call({data: b64(pdf('INVOICE 4471 from Brooklyn Lumber: 40 sheets 5/8 Type X drywall, total due $1,240.00, net 30')), mime: 'application/pdf', name: 'inv.pdf'});
ok(s === 200 && /INVOICE 4471/.test(j.text) && /\$1,240\.00/.test(j.text) && j.how === 'pdf text', `a text PDF is read here: ${JSON.stringify(j).slice(0, 160)}`);
ok(W.calls.length === 0, 'and costs nothing (no model call)');
[s, j] = await call({data: b64(docx('Quote Q-118: millwork for 121 State, $18,400, 8 weeks')), mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', name: 'quote.docx'});
ok(s === 200 && /Quote Q-118/.test(j.text) && j.how === 'word', `a Word document is read here: ${JSON.stringify(j).slice(0, 120)}`);
[s, j] = await call({data: b64(pdf(' ')), mime: 'application/pdf', name: 'scan.pdf'});
ok(s === 200 && /Home Depot/.test(j.text) && j.how === 'scan read by the model', `a scan goes to the model: ${JSON.stringify(j).slice(0, 120)}`);
const sent = W.calls[0];
ok(sent.model === 'claude-haiku-5-5' && sent.messages[0].content[0].type === 'document', 'the small model, with the PDF as a document');
ok(W.logged.length === 1 && W.logged[0].tier === 'small:doctext' && W.logged[0].cost_usd > 0, 'logged as a reader call with its cost');
[s, j] = await call({data: b64(Buffer.from([0xff, 0xd8, 0xff, 0xe0, 1, 2, 3])), mime: 'image/jpeg', name: 'receipt.jpg'});
ok(s === 200 && /Total \$87\.40/.test(j.text) && W.calls[1].messages[0].content[0].type === 'image', 'a photo is read by the model');
W.spend = 999; const before = W.calls.length;
[s, j] = await call({data: b64(pdf(' ')), mime: 'application/pdf', name: 'scan2.pdf'});
ok(s === 429 && /budget/i.test(j.note || '') && W.calls.length === before, 'over the firm cap: no model call, and it says so');
W.spend = 0;
[s, j] = await call({data: b64(Buffer.from('a,b\n1,2')), mime: 'text/csv', name: 'x.csv'}); ok(j.text === 'a,b\n1,2', 'CSV and text pass through');
[s, j] = await call({data: b64(Buffer.from('PK..')), mime: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', name: 'x.xlsx'}); ok(!j.text && /CSV/.test(j.note), 'a spreadsheet gets a plain note');
[s, j] = await call({data: b64(Buffer.from('x')), mime: 'image/heic', name: 'IMG_1.HEIC'}); ok(!j.text && /Most Compatible/.test(j.note), 'an iPhone HEIC photo gets a plain note');
[s, j] = await call({data: b64(Buffer.alloc(5e6)), mime: 'application/pdf', name: 'big.pdf'}); ok(s === 413 && /4\.5 MB/.test(j.note), 'too large: says so');
[s, j] = await call({data: b64(Buffer.from('not a pdf')), mime: 'application/pdf', name: 'bad.pdf'}); ok(s === 200 && !j.text && /could not open/.test(j.note), `a broken file gets a note, not a crash: ${j.note}`);
console.log('ALL PASS', `(${n} checks)`);
