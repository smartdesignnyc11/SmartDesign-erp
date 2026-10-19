// A small, dependency-free reader for .xlsx: the zip's central directory, then the workbook, shared strings and
// sheets as rows of text. It reads cell values only (no formulas run, no macros, no external links), refuses
// encrypted or zip64 files, and stops at fixed limits so a hostile file cannot exhaust the function.
import zlib from 'node:zlib';
const LIMITS = {entries: 2000, unpacked: 40e6, sheets: 20, rows: 5000, cols: 60};
function unzip(buf) {
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 66000); i--) if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  if (eocd < 0) throw new Error('not a zip file');
  const count = buf.readUInt16LE(eocd + 10), cdOff = buf.readUInt32LE(eocd + 16);
  if (count > LIMITS.entries || cdOff === 0xffffffff) throw new Error('too many parts');
  const files = {}; let p = cdOff, total = 0;
  for (let n = 0; n < count; n++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) throw new Error('damaged zip');
    const flags = buf.readUInt16LE(p + 8), method = buf.readUInt16LE(p + 10), csize = buf.readUInt32LE(p + 20), usize = buf.readUInt32LE(p + 24);
    const nl = buf.readUInt16LE(p + 28), xl = buf.readUInt16LE(p + 30), cl = buf.readUInt16LE(p + 32), lo = buf.readUInt32LE(p + 42);
    const name = buf.toString('utf8', p + 46, p + 46 + nl); p += 46 + nl + xl + cl;
    if (flags & 1) throw new Error('the spreadsheet is password protected');
    if (!/^(xl\/(workbook\.xml|sharedStrings\.xml|worksheets\/sheet\d+\.xml|_rels\/workbook\.xml\.rels))$/.test(name)) continue;
    total += usize; if (total > LIMITS.unpacked) throw new Error('the spreadsheet unpacks too large');
    const ln = buf.readUInt16LE(lo + 26), lx = buf.readUInt16LE(lo + 28), start = lo + 30 + ln + lx, data = buf.subarray(start, start + csize);
    files[name] = method === 0 ? data.toString('utf8') : method === 8 ? zlib.inflateRawSync(data, {maxOutputLength: Math.max(usize, 1) + 1024}).toString('utf8') : '';
  }
  return files;
}
const unesc = s => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d)).replace(/&amp;/g, '&');
const texts = x => (x.match(/<t[^>]*>([\s\S]*?)<\/t>/g) || []).map(t => unesc(t.replace(/<t[^>]*>|<\/t>/g, ''))).join('');
const colOf = ref => { let c = 0; for (const ch of String(ref).replace(/\d+/g, '')) c = c * 26 + (ch.charCodeAt(0) - 64); return c - 1; };
export function xlsxText(buf) {
  const f = unzip(buf);
  if (!f['xl/workbook.xml']) throw new Error('not a spreadsheet');
  const shared = (f['xl/sharedStrings.xml'] || '').match(/<si>[\s\S]*?<\/si>/g)?.map(texts) || [];
  const rels = Object.fromEntries([...(f['xl/_rels/workbook.xml.rels'] || '').matchAll(/<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"/g)].map(m => [m[1], m[2].replace(/^\/?(xl\/)?/, 'xl/')]));
  const sheets = [...f['xl/workbook.xml'].matchAll(/<sheet[^>]*name="([^"]*)"[^>]*r:id="([^"]+)"/g)].slice(0, LIMITS.sheets);
  const out = [];
  for (const [, name, rid] of sheets) {
    const xml = f[rels[rid]] || ''; if (!xml) continue;
    const rows = [];
    for (const r of (xml.match(/<row[^>]*>[\s\S]*?<\/row>/g) || []).slice(0, LIMITS.rows)) {
      const cells = [];
      for (const c of r.match(/<c [^>]*(?:\/>|>[\s\S]*?<\/c>)/g) || []) {
        const ref = (c.match(/ r="([A-Z]+\d+)"/) || [])[1], t = (c.match(/ t="([^"]+)"/) || [])[1] || '', v = (c.match(/<v>([\s\S]*?)<\/v>/) || [])[1];
        const col = ref ? colOf(ref) : cells.length; if (col >= LIMITS.cols) continue;
        cells[col] = t === 's' ? (shared[+v] || '') : t === 'inlineStr' ? texts(c) : t === 'b' ? (v === '1' ? 'TRUE' : 'FALSE') : v != null ? unesc(v) : '';
      }
      if (cells.some(x => x !== undefined && x !== '')) rows.push(Array.from(cells, x => x ?? '').join(' | '));
    }
    out.push(`Sheet: ${unesc(name)}\n${rows.join('\n')}`);
  }
  return out.join('\n\n');
}
