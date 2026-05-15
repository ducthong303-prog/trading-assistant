/**
 * tv_collect.js — One-shot TradingView data collector (zero Claude tokens)
 * ═══════════════════════════════════════════════════════════════════════
 * Kết nối CDP một lần, thu thập 6 loại data song song, xuất JSON ra stdout.
 * Được gọi bởi market_monitor.py hoặc tv_auto_scan.sh khi mode=auto.
 *
 * Usage:
 *   node tv_collect.js [PAIR]       → JSON ra stdout
 *   node tv_collect.js BTCUSD       → collect BTCUSD
 *   node tv_collect.js              → default BTCUSD
 *
 * Exit codes: 0 = success, 1 = error (JSON error trên stdout), 2 = CDP fail
 */

import { connect, disconnect, evaluate, safeString } from './src/connection.js';
import {
  getQuote,
  getStudyValues,
  getPineLines,
  getPineLabels,
} from './src/core/data.js';

const PAIR    = process.argv[2] || 'BTCUSD';
const TIMEOUT = 20_000;  // 20s hard timeout

// ── Timeout guard ─────────────────────────────────────────────────────────────
const timer = setTimeout(() => {
  process.stderr.write(`[tv_collect] TIMEOUT after ${TIMEOUT}ms\n`);
  process.exit(2);
}, TIMEOUT);
timer.unref();

// ── Main ─────────────────────────────────────────────────────────────────────
async function run() {
  try {
    await connect();
  } catch (err) {
    process.stderr.write(`[tv_collect] CDP connect failed: ${err.message}\n`);
    process.stdout.write(JSON.stringify({ error: 'CDP_CONNECT_FAIL', message: err.message }) + '\n');
    process.exit(2);
  }

  // Điều hướng chart sang pair nếu cần
  try {
    const curSymbol = await evaluate(`
      (function() {
        try { return window.TradingViewApi._activeChartWidgetWV.value().symbol(); }
        catch(e) { return null; }
      })()`
    );
    if (curSymbol && curSymbol.toUpperCase() !== PAIR.toUpperCase()) {
      await evaluate(`
        (function() {
          try { window.TradingViewApi._activeChartWidgetWV.value().setSymbol(${safeString(PAIR)}, null); }
          catch(e) {}
        })()`
      );
      // Đợi chart reload (ngắn thôi — collector chạy định kỳ, không cần chờ sâu)
      await new Promise(r => setTimeout(r, 1500));
    }
  } catch { /* nếu không set được thì dùng chart hiện tại */ }

  // ── Thu thập song song — 1 CDP WebSocket, 6 JS calls ─────────────────────
  const [quote, studyVals, smcLabels, po3Labels, vpLines, liqLabels] = await Promise.allSettled([
    getQuote(),
    getStudyValues(),
    getPineLabels({ study_filter: 'Smart Money', max_labels: 10 }),
    getPineLabels({ study_filter: 'HTF Power',   max_labels: 4  }),
    getPineLines({ study_filter: 'Volume Profile' }),
    getPineLabels({ study_filter: 'Liquidity',   max_labels: 20 }),
  ]);

  const unwrap = (settled) => settled.status === 'fulfilled' ? settled.value : null;

  const q = unwrap(quote);
  const price = q?.last ?? q?.close ?? 0;

  // Chuyển nested CLI response → flat format mà tv_indicator_parser.py mong đợi
  // smc/po3/liq: [{text, price}], vp: [number], study_values: [{name, values}]
  const extractLabels = (r) => (r?.studies ?? []).flatMap(s => s.labels ?? []);
  const extractLines  = (r) => (r?.studies ?? []).flatMap(s => s.levels ?? s.lines ?? []);
  const extractStudies = (r) => r?.studies ?? [];

  const output = {
    symbol:       PAIR,
    price,
    study_values: extractStudies(unwrap(studyVals)),
    smc_labels:   extractLabels(unwrap(smcLabels)),
    po3_labels:   extractLabels(unwrap(po3Labels)),
    vp_lines:     extractLines(unwrap(vpLines)),
    liq_labels:   extractLabels(unwrap(liqLabels)),
  };

  await disconnect();
  clearTimeout(timer);

  process.stdout.write(JSON.stringify(output) + '\n');
  process.exit(0);
}

run().catch(err => {
  process.stderr.write(`[tv_collect] Unexpected error: ${err.message}\n`);
  process.stdout.write(JSON.stringify({ error: 'UNEXPECTED', message: err.message }) + '\n');
  process.exit(1);
});
