// /api/doctext: the document reader. The app sends a file ({data: base64, mime, name}) and gets its text back.
// - PDFs with a text layer and Word documents are read here, at no cost.
// - Scanned PDFs and photos (receipts, slips, certificates) are read by the small Claude model through the same
//   capped, logged door as every AI call, and the answer says so.
// - Anything else answers with a plain note of what to do, never a guess.
// The file is read in memory and not kept.
import {caller, json} from './lib/auth.mjs';
import {claude} from './ai.mjs';
const MAX_TEXT = 200000;
const IMAGES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/gif']);
const kindOf = (mime, name) => {
  const m = String(mime || '').toLowerCase(), n = String(name || '').toLowerCase();
  if (m === 'application/pdf' || n.endsWith('.pdf')) return 'pdf';
  if (m.includes('wordprocessingml') || n.endsWith('.docx')) return 'docx';
  if (IMAGES.has(m) || /\.(jpe?g|png|webp|gif)$/.test(n)) return 'image';
  if (m.includes('spreadsheetml') || /\.(xlsx|xls)$/.test(n)) return 'sheet';
  if (m.startsWith('text/') || /\.(txt|csv|md|html?)$/.test(n)) return 'text';
  if (/\.(heic|heif)$/.test(n) || m.includes('heic')) return 'heic';
  return 'other';
};
const clean = t => String(t || '').replace(/\r/g, '').replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim().slice(0, MAX_TEXT);
const mediaOf = (mime, name) => IMAGES.has(String(mime).toLowerCase()) ? String(mime).toLowerCase()
  : /\.png$/i.test(name) ? 'image/png' : /\.webp$/i.test(name) ? 'image/webp' : /\.gif$/i.test(name) ? 'image/gif' : 'image/jpeg';

export async function pdfText(buf) {
  const {extractText, getDocumentProxy} = await import('unpdf');
  const pdf = await getDocumentProxy(new Uint8Array(buf));
  const {text, totalPages} = await extractText(pdf, {mergePages: true});
  return {text: clean(text), pages: totalPages};
}
export async function docxText(buf) {
  const mammoth = (await import('mammoth')).default;
  return clean((await mammoth.extractRawText({buffer: buf})).value);
}
async function readByModel(user, profile, block, name) {
  const r = await claude(user, profile, {tier: 'small', purpose: 'doctext', max_tokens: 4000, messages: [{role: 'user', content: [block,
    {type: 'text', text: `Transcribe all the text in this document (${name || 'a file'}) exactly as written, keeping tables as rows with the columns separated by " | ". Write only the text: no commentary. If nothing is legible, write "(no legible text)".`}]}]});
  let j = {}; try { j = JSON.parse(r.text); } catch {}
  if (r.status !== 200) return {error: (j.error && (j.error.message || j.error)) || `the reader could not use the model (${r.status})`, status: r.status};
  const text = (j.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n');
  return {text: /^\(no legible text\)$/.test(text.trim()) ? '' : clean(text)};
}

export default async (req) => {
  if (req.method !== 'POST') return json(405, {error: 'POST only'});
  const who = await caller(req);
  if (who instanceof Response) return who;
  let b; try { b = await req.json(); } catch { return json(400, {error: 'bad JSON'}); }
  if (!b || !b.data) return json(400, {error: 'data required'});
  const buf = Buffer.from(String(b.data), 'base64');
  if (buf.length > 4.5e6) return json(413, {note: 'This file is over 4.5 MB, too large to read here. Open it and save the pages that matter as a smaller PDF.'});
  const kind = kindOf(b.mime, b.name), name = b.name || '';
  try {
    if (kind === 'text') return json(200, {text: clean(String(b.mime || '').includes('html') || /\.html?$/i.test(name) ? buf.toString('utf8').replace(/<style[\s\S]*?<\/style>|<script[\s\S]*?<\/script>/gi, '').replace(/<[^>]+>/g, ' ') : buf.toString('utf8')), how: 'text'});
    if (kind === 'docx') return json(200, {text: await docxText(buf), how: 'word'});
    if (kind === 'pdf') {
      const p = await pdfText(buf);
      if (p.text.replace(/\s/g, '').length >= 40 * Math.max(1, Math.min(p.pages, 3))) return json(200, {text: p.text, pages: p.pages, how: 'pdf text'});
      // A scan: no text layer worth the name. The model reads the pages.
      const m = await readByModel(who.user, who.profile, {type: 'document', source: {type: 'base64', media_type: 'application/pdf', data: buf.toString('base64')}}, name);
      return m.error ? json(m.status === 429 ? 429 : 200, {text: '', note: 'This PDF is a scan and could not be read: ' + m.error}) : json(200, {text: m.text, pages: p.pages, how: 'scan read by the model'});
    }
    if (kind === 'image') {
      if (buf.length > 3.7e6) return json(413, {note: 'This photo is over 3.7 MB: take it again at a lower size, or crop it to the page.'});
      const m = await readByModel(who.user, who.profile, {type: 'image', source: {type: 'base64', media_type: mediaOf(b.mime, name), data: buf.toString('base64')}}, name);
      return m.error ? json(m.status === 429 ? 429 : 200, {text: '', note: 'This photo could not be read: ' + m.error}) : json(200, {text: m.text, how: 'photo read by the model'});
    }
    if (kind === 'heic') return json(200, {text: '', note: 'iPhone HEIC photos are not read yet: set Camera › Formats › Most Compatible, or share the photo as a JPEG.'});
    if (kind === 'sheet') return json(200, {text: '', note: 'Spreadsheets are not read yet: save it as CSV and attach that.'});
    return json(200, {text: '', note: `This kind of file (${b.mime || name || 'unknown'}) is not read yet.`});
  } catch (e) {
    return json(200, {text: '', note: 'The reader could not open this file: ' + String(e.message || e).slice(0, 160)});
  }
};
export const config = {path: '/api/doctext'};
