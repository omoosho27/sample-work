export const WARNING='GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.';
export const keys=['brand','type','abv','volume','producer','origin'];
export const labels={brand:'Brand name',type:'Class / type',abv:'Alcohol content',volume:'Net contents',producer:'Producer / address',origin:'Country of origin'};
export const norm=s=>String(s).normalize('NFKC').toLowerCase().replace(/[’‘]/g,"'").replace(/\s+/g,' ').trim();
const tokens=s=>norm(s).replace(/'/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const has=(text,value)=>(' '+tokens(text)+' ').includes(' '+tokens(value)+' ');
export function volumes(s){return [...s.matchAll(/(\d+(?:\.\d+)?)\s*(ml|millilit(?:er|re)s?|l|lit(?:er|re)s?|fl\.?\s*oz\.?)/gi)].map(m=>({raw:m[0],n:Number(m[1])*(/^ml|^mill/i.test(m[2])?1:/^fl/i.test(m[2])?29.5735295625:1000)}));}
export function verify(text,expected,confidence=100,format='unknown'){
 const rows=[]; const row=(key,status,observed,note)=>rows.push({key,label:labels[key]||key,status,expected:expected[key]||'',observed,note});
 for(const key of keys){const value=String(expected[key]||'').trim(); if(!value){row(key,'review','Not supplied','No application value supplied.');continue;}
 if(key==='abv') {const values=[...text.matchAll(/(\d+(?:\.\d+)?)\s*%/g)];const wanted=Number(value.replace(/%|\s/g,'')); const hit=values.find(m=>Number(m[1])===wanted);row(key,hit?'match':values.length?'mismatch':'review',hit?.[0]||values.map(m=>m[0]).join(', ')||'Not read',hit?'Percentage matches.':values.length?'Percentage differs from the application.':'Could not read a percentage.');}
 else if(key==='volume'){const values=volumes(text),wanted=volumes(value)[0];const hit=wanted&&values.find(v=>Math.abs(v.n-wanted.n)<=Math.max(.1,wanted.n*.002));row(key,hit?'match':values.length&&wanted?'mismatch':'review',hit?.raw||values.map(v=>v.raw).join(', ')||'Not read',hit?'Equivalent volume matches.':!wanted?'Use a value with units, for example 750 mL.':values.length?'Volume differs from the application.':'Could not read net contents.');}
 else {const hit=has(text,value);row(key,hit?'match':'review',hit?value:'Not found',hit?'Matches, ignoring letter case and punctuation.':'Expected wording not found. Check the image and extracted text.');}}
 const start=text.search(/government\s+warning\s*:/i);const warn=start<0?'':text.slice(start);const exact=norm(warn).startsWith(norm(WARNING));const caps=/^GOVERNMENT\s+WARNING\s*:/.test(warn);
 rows.push({key:'warning',label:'Warning wording',status:exact?'match':'review',expected:WARNING,observed:warn||'Not read',note:exact?'All words and punctuation match; line breaks and case ignored.':'Missing or different wording. Review OCR against the image.'});
 rows.push({key:'caps',label:'Warning heading capitals',status:start<0?'review':caps?'match':'mismatch',expected:'GOVERNMENT WARNING:',observed:warn.match(/^.*?:/)?.[0]||'Not read',note:caps?'Heading is uppercase.':'Heading must be uppercase; confirm the OCR reading.'});
 rows.push({key:'format',label:'Warning formatting',status:format==='yes'?'match':format==='no'?'mismatch':'review',expected:'Bold heading; regular body; separate continuous paragraph',observed:format==='unknown'?'Needs visual confirmation':format==='yes'?'Confirmed by reviewer':'Issue reported by reviewer',note:'Reviewer check: OCR cannot reliably verify typography or physical type size.'});
 if(confidence<75)for(const r of rows)if(r.status==='match'&&r.key!=='format'){r.status='review';r.note='Low OCR confidence. Confirm this reading against the image.';}
 return {rows,status:rows.some(r=>r.status==='mismatch')?'mismatch':rows.some(r=>r.status==='review')?'review':'match',confidence};
}
