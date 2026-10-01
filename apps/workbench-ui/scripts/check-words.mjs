// Checks the display formatters in src/lib (words.ts, csv.ts) on fixed cases.
//   node scripts/check-words.mjs        exit 1 on any failure
import { build } from "esbuild";
async function load(file) {
  const out = await build({ entryPoints: [file], bundle: true, write: false, format: "esm", platform: "neutral" });
  return import("data:text/javascript;base64," + Buffer.from(out.outputFiles[0].text).toString("base64"));
}
const { amountsInWords } = await load("src/lib/words.ts");
const { toCsv } = await load("src/lib/csv.ts");
const amounts = [
  ["AS 2401.05", "AS 2401.05"], ["account 1200.10 moved", "account 1200.10 moved"],
  ["date 2026.06.30", "date 2026.06.30"], ["rate 24.2 %", "rate 24.2 %"],
  ["24.2 percent", "24.2 percent"], ["current ratio 1.5", "current ratio 1.5"],
  ["Section 1.2", "Section 1.2"], ["DSO 45.3 days", "DSO 45.3 days"],
  ["2.0 × materiality", "2.0 × materiality"], ["floor 1.20", "floor 1.20"],
  ["invoice MC-25009", "invoice MC-25009"], ["ends 5.50.", "ends 5.50."],
  ["total 7325.0 around threshold 2500.0", "total 7,325.00 around threshold 2,500.00"],
  ["moved -374240.0 (-9.6%)", "moved -374,240.00 (-9.6%)"],
  ["paid 18432.50 on 2026-03-06", "paid 18,432.50 on 2026-03-06"],
  ["moved 36820.83 (24.2%)", "moved 36,820.83 (24.2%)"],
  ["client misstatement 620.0 (over", "client misstatement 620.0 (over"],
];
const csv = [
  [["=HYPERLINK(1)"], "'=HYPERLINK(1)"], [["@SUM(A1)"], "'@SUM(A1)"], [["+1"], "'+1"],
  [["-1840.00"], "-1840.00"], [["-1,234.50"], "\"-1,234.50\""], [["-note"], "'-note"],
  [[" =1"], "' =1"], [["|cmd"], "'|cmd"], [["＝1"], "'＝1"], [["a,b"], "\"a,b\""],
  [[-25000], "-25000"],
];
let bad = 0;
for (const [input, want] of amounts) {
  const got = amountsInWords(input);
  if (got !== want) { bad++; console.log("FAIL amount", JSON.stringify(input), "->", JSON.stringify(got), "want", JSON.stringify(want)); }
}
for (const [row, want] of csv) {
  const got = toCsv(["h"], [row]).split("\r\n")[1];
  if (got !== want) { bad++; console.log("FAIL csv", JSON.stringify(row), "->", JSON.stringify(got), "want", JSON.stringify(want)); }
}
console.log(`check-words: ${amounts.length + csv.length - bad} of ${amounts.length + csv.length} ok`);
process.exit(bad ? 1 : 0);
