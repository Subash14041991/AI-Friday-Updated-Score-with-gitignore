// Render this simple Mermaid subset from the generated D3 into SVG.
// Unsupported syntax fails rather than silently changing the architecture.
const fs = require('node:fs');
const {instance} = require('./node_runtime.cjs').load('@viz-js/viz');
const [source, output] = process.argv.slice(2);
const md = fs.readFileSync(source, 'utf8');
const blocks = [...md.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)];
if (blocks.length !== 1) throw new Error('Expected one Mermaid diagram.');
const groups = [], nodes = [], edges = [];
let group = null;
for (const raw of blocks[0][1].split('\n')) {
  const line = raw.trim();
  if (!line || line === 'flowchart LR') continue;
  let match;
  if ((match = line.match(/^subgraph (\w+)\["([^"]+)"\]$/))) {
    group = {id:match[1], label:match[2]}; groups.push(group);
  } else if (line === 'end') { group = null;
  } else if ((match = line.match(/^(\w+)\["([^"]+)"\]$/))) {
    nodes.push({id:match[1], label:match[2].replace(/<br\s*\/?\s*>/g, '\n'), group:group?.id});
  } else if ((match = line.match(/^(\w+)\s+(-->|<-->)\|"([^"]+)"\|\s+(\w+)$/))) {
    edges.push({from:match[1], both:match[2] === '<-->', label:match[3], to:match[4]});
  } else throw new Error('Unsupported diagram syntax: ' + line);
}
const ids = new Set(nodes.map(n => n.id));
for (const edge of edges) if (!ids.has(edge.from) || !ids.has(edge.to)) throw new Error('Unknown endpoint.');
for (const node of nodes) if (!edges.some(e => e.from === node.id || e.to === node.id)) throw new Error('Disconnected node.');
const q = value => JSON.stringify(value);
let dot = 'digraph Architecture { graph [rankdir=LR, bgcolor="transparent", pad=0.25, nodesep=0.5, ranksep=0.8, splines=polyline, fontname="Arial", fontsize=22]; node [shape=box, style="rounded,filled", fillcolor="white", color="#50798c", fontcolor="#173047", fontname="Arial", fontsize=20, margin="0.2,0.15", penwidth=1.5]; edge [color="#315b73", fontcolor="#315b73", fontname="Arial", fontsize=16, penwidth=1.7, arrowsize=0.8];\n';
for (const g of groups) {
  dot += `subgraph cluster_${g.id} { label=${q(g.label)}; style="rounded,filled"; color="#a4becb"; fillcolor="#f1f7fa"; margin=20;\n`;
  if (g.id === groups[0]?.id) dot += 'rank=same;\n';
  for (const n of nodes.filter(n=>n.group===g.id)) dot += `${n.id} [label=${q(n.label)}];\n`;
  dot += '}\n';
}
for (const n of nodes.filter(n=>!n.group)) dot += `${n.id} [label=${q(n.label)}];\n`;
// Keep the source's first group (people/channels) on the left. Return/user
// branches retain their direction but do not reverse the main layout order.
const firstGroup = groups[0]?.id;
const people = new Set(nodes.filter(n=>n.group===firstGroup).map(n=>n.id));
for (const e of edges) dot += `${e.from} -> ${e.to} [label=${q(e.label)}${e.both?', dir=both':''}${people.has(e.to)?', constraint=false':''}];\n`;
dot += '}';
(async()=>{
  const viz = await instance();
  const svg = viz.renderString(dot, {format:'svg'});
  fs.writeFileSync(output, svg);
  console.log(`Rendered ${nodes.length} nodes and ${edges.length} flows from the D3 diagram source.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
