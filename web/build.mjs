// Compila web/src en un único HTML autocontenido: web/calculadora_supervivencia.html
// Funciona en Windows, macOS y Linux:   node build.mjs
import { build } from "esbuild";
import { readFileSync, writeFileSync } from "node:fs";

const res = await build({
  entryPoints: ["src/main.jsx"],
  bundle: true,
  minify: true,
  format: "iife",
  write: false,
  loader: { ".js": "jsx" },
  define: { "process.env.NODE_ENV": '"production"' },
});
const js = res.outputFiles[0].text;
const css = readFileSync("src/styles.css", "utf8");
if (js.includes("</script")) throw new Error("El bundle contiene </script>: no se puede incrustar.");

const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Calculadora de supervivencia</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700&family=STIX+Two+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>${css}</style>
</head>
<body>
<div id="root"></div>
<script>${js}</script>
</body>
</html>
`;
writeFileSync("calculadora_supervivencia.html", html);
console.log(`calculadora_supervivencia.html generado (${(html.length / 1024).toFixed(0)} kB)`);
