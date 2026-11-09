import json,re,subprocess,sys
V=sys.argv[1]
beats=json.load(open(f'{V}/build/beats.json'))
R=[(r'\bSS\b','S.S.'),(r'\bSA\b','S.A.'),(r'\bSD\b','S.D.'),('NSDAP','N.S.D.A.P.'),('RSHA','R.S.H.A.'),('WVHA','W.V.H.A.'),
   ('Röhm','Rurm'),('Reichsführer','Reichs-fuehrer'),('Führer','Fuehrer'),('Bełżec','Belzec'),('Sobibór','Sobibor'),
   ('Lüneburg','Luneburg'),('Stoßtrupp','Shtoss-troop'),('Schutzstaffel','Shoots-shtaffel'),('Sturmabteilung','Shturm-ab-tile-ung'),
   ('Wewelsburg','Vay-vels-burg'),('Einsatzgruppen','Ine-zats-groupen'),('Totenkopfverbände','Toten-kopf-fer-benda'),
   ('Geheime Staatspolizei','Geheimeh Shtahts-polizei'),('Sicherheitsdienst','Zicker-heits-deenst'),('Kristallnacht','Kristall-nakht'),
   ('Verfügungstruppe','Fer-fuegungs-truppe'),('Lebensborn','Lay-bens-born'),('Ahnenerbe','Ah-nen-erbe'),('–',', '),('—',', ')]
for i,b in enumerate(beats):
  t=b['text']
  if not t: continue
  for a,c in R: t=re.sub(a,c,t)
  subprocess.run([sys.executable,'-m','piper','-m',f'{V}/voice/v.onnx','-f',f'{V}/audio/{i:02d}.wav','--length-scale','1.08','--sentence-silence','0.35'],input=t.encode(),check=True,capture_output=True)
  print(i,end=' ',flush=True)
