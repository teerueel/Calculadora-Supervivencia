set -e
cd /home/claude/web
npx esbuild src/main.jsx --bundle --minify --format=iife --define:process.env.NODE_ENV='"production"' --outfile=build/app.js --log-level=warning
python3 - <<'P'
js=open('/home/claude/web/build/app.js').read(); css=open('/home/claude/web/src/styles.css').read()
html=f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Calculadora de supervivencia</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700&family=STIX+Two+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<div id="root"></div>
<script>{js.replace("</script>","<\\/script>")}</script>
</body>
</html>'''
open('/mnt/user-data/outputs/calculadora_supervivencia.html','w').write(html)
P
