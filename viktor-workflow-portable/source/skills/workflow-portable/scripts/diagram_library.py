#!/usr/bin/env python3
"""Bounded offline diagram catalog and original synthetic SVG/draw.io/BPMN exports.

No third-party renderer, installer, browser, network, environment or project scanning.
Checks are deliberately narrower than a complete BPMN/UML/architecture proof.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT/'references/diagrams'
SVG = 'http://www.w3.org/2000/svg'
BPMN = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
BPMNDI = 'http://www.omg.org/spec/BPMN/20100524/DI'
DC = 'http://www.omg.org/spec/DD/20100524/DC'
DI = 'http://www.omg.org/spec/DD/20100524/DI'
ID = re.compile(r'^[a-z][a-z0-9_-]{0,63}$')


def require(ok, message):
    if not ok: raise ValueError(message)


def identifier(value):
    require(isinstance(value, str) and ID.fullmatch(value), 'invalid id')


def contained(root, relative):
    p = Path(relative)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in str(p), 'unsafe library path')
    target = root/p
    require(root.resolve() in target.resolve().parents, 'library escape')
    require(not any(x.is_symlink() for x in [target,*target.parents] if root in x.parents), 'symlink in library')
    return target


def load(path):
    require(path.stat().st_size <= 1024*1024, 'oversized model')
    return json.loads(path.read_text())


def validate(model):
    for k in ('id','title','family','notation','question','scope','audience','legend','current_target','owner','reviewed_at','update_trigger','limitations','nodes','edges','zones','canvas'):
        require(k in model, 'missing model field '+k)
    identifier(model['id'])
    require(model['current_target'] in ('synthetic-reference','current','target'), 'view status required')
    require(model['family'] in ('c4','network','security','bpmn','sequence','state','erd','component','reliability'), 'unsupported family')
    for k in ('title','notation','question','scope','audience','legend','owner','reviewed_at','update_trigger','limitations'):
        require(isinstance(model[k],str) and 0<len(model[k])<=1500, 'empty model metadata')
    require(len(model['nodes']) <= 60 and len(model['edges']) <= 120 and len(model['zones']) <= 12, 'model too large; decompose views')
    w,h=model['canvas']; require(100<=w<=2400 and 100<=h<=2000, 'invalid canvas')
    ids=set(); zones={}
    for z in model['zones']:
        identifier(z['id']); require(z['id'] not in ids,'duplicate id'); ids.add(z['id']);zones[z['id']]=z
        require(z['x']>=0 and z['y']>=0 and z['width']>0 and z['height']>0 and z['x']+z['width']<=w and z['y']+z['height']<=h,'zone outside canvas')
    nodes={}
    for n in model['nodes']:
        identifier(n['id']);require(n['id'] not in ids,'duplicate id');ids.add(n['id']);nodes[n['id']]=n
        require(isinstance(n['label'],str) and n['label'] and len(n['label'])<=250,'invalid node label')
        require(n['zone'] is None or n['zone'] in zones,'unknown zone')
        require(n['x']>=0 and n['y']>=0 and n['width']>=20 and n['height']>=20 and n['x']+n['width']<=w and n['y']+n['height']<=h,'node outside canvas')
        if n['zone']:
            z=zones[n['zone']]
            require(n['x']>=z['x'] and n['y']>=z['y']+26 and n['x']+n['width']<=z['x']+z['width'] and n['y']+n['height']<=z['y']+z['height'],'node outside zone')
    require(nodes,'empty model')
    for edge in model['edges']:
        identifier(edge['id']);require(edge['id'] not in ids,'duplicate id');ids.add(edge['id'])
        require(edge['source'] in nodes and edge['target'] in nodes,'dangling edge')
        require(isinstance(edge['label'],str) and len(edge['label'])<=220,'invalid edge label')
        require([edge['source'],edge['target']] not in model.get('constraints',{}).get('forbidden_direct_flows',[]),'declared forbidden direct flow')
        if model['family']=='bpmn':
            a,b=nodes[edge['source']],nodes[edge['target']]
            if edge['kind']=='message':require(a['zone']!=b['zone'],'message must cross participants')
            else:require(edge['kind']=='sequence' and a['zone']==b['zone'],'sequence must remain within participant')
    for a in model['nodes']:
        for b in model['nodes']:
            if a['id']>=b['id'] or a.get('attached_to')==b['id'] or b.get('attached_to')==a['id']:continue
            require(not (a['x']<b['x']+b['width'] and b['x']<a['x']+a['width'] and a['y']<b['y']+b['height'] and b['y']<a['y']+a['height']),'overlapping nodes')
    if model['family']=='sequence':
        ys=[e['y'] for e in model['edges']];require(ys==sorted(set(ys)),'sequence message order invalid')
    if model['family']=='bpmn':
        for n in nodes.values():
            require(n['zone'] in zones,'BPMN needs participant')
            incoming=[e for e in model['edges'] if e['kind']=='sequence' and e['target']==n['id']]
            outgoing=[e for e in model['edges'] if e['kind']=='sequence' and e['source']==n['id']]
            if n['kind']=='start':require(not incoming and outgoing,'start event flow invalid')
            elif n['kind']=='end':require(incoming and not outgoing,'end event flow invalid')
            elif n['kind']=='timer':require(n.get('attached_to') in nodes and nodes[n['attached_to']]['zone']==n['zone'] and not incoming and outgoing,'boundary timer invalid')
            else:require(incoming and outgoing,'unconnected BPMN activity/gateway')
            if n['kind']=='xor' and len(outgoing)>1:
                require(sum(bool(e.get('default')) for e in outgoing)==1,'XOR needs one explicit default')
                require(all(e.get('default') or e.get('condition') for e in outgoing),'XOR branch missing condition')
        for zone in zones:
            members=[n for n in nodes.values() if n['zone']==zone]
            starts={n['id'] for n in members if n['kind']=='start'}
            ends={n['id'] for n in members if n['kind']=='end'}
            require(starts and ends,'participant needs start/end')
            reachable=set(starts)
            for _ in members:
                reachable.update(e['target'] for e in model['edges'] if e['kind']=='sequence' and e['source'] in reachable)
                reachable.update(n['id'] for n in members if n.get('attached_to') in reachable)
            require({n['id'] for n in members}<=reachable and ends<=reachable,'unreachable BPMN node')
    return model


def points(model, edge):
    if edge.get('points'):return edge['points']
    nodes={n['id']:n for n in model['nodes']};a,b=nodes[edge['source']],nodes[edge['target']]
    if model['family']=='sequence':return [(a['x']+a['width']/2,edge['y']),(b['x']+b['width']/2,edge['y'])]
    if abs(a['x']-b['x'])>=abs(a['y']-b['y']):
        if b['x']>=a['x']:return [(a['x']+a['width'],a['y']+a['height']/2),(b['x'],b['y']+b['height']/2)]
        return [(a['x'],a['y']+a['height']/2),(b['x']+b['width'],b['y']+b['height']/2)]
    if b['y']>=a['y']:return [(a['x']+a['width']/2,a['y']+a['height']),(b['x']+b['width']/2,b['y'])]
    return [(a['x']+a['width']/2,a['y']),(b['x']+b['width']/2,b['y']+b['height'])]


def text(parent,label,x,y,size=12,anchor='middle',color='#172B4D'):
    lines=label.split('\n')
    for i,line in enumerate(lines):
        node=ET.SubElement(parent,'text',{'x':str(x),'y':str(y+i*(size+3)),'font-family':'Arial, sans-serif','font-size':str(size),'text-anchor':anchor,'fill':color})
        node.text=line


def svg(model):
    validate(model);w,h=model['canvas']
    root=ET.Element('svg',{'xmlns':SVG,'width':str(w),'height':str(h),'viewBox':f'0 0 {w} {h}','role':'img','aria-labelledby':'title desc'})
    ET.SubElement(root,'title',{'id':'title'}).text=model['title']
    ET.SubElement(root,'desc',{'id':'desc'}).text=model['question']+' | '+model['legend']
    ET.SubElement(root,'metadata').text=json.dumps({'model_id':model['id'],'source_sha256':hashlib.sha256(json.dumps(model,sort_keys=True).encode()).hexdigest(),'exporter':'original offline SVG; not a third-party engine render'})
    ET.SubElement(root,'rect',{'width':str(w),'height':str(h),'fill':'#FFFFFF'})
    text(root,model['title'],24,29,19,'start');text(root,'SYNTHETIC REFERENCE | '+model['notation'],24,51,10,'start','#586B82')
    for zone in model['zones']:
        ET.SubElement(root,'rect',{'x':str(zone['x']),'y':str(zone['y']),'width':str(zone['width']),'height':str(zone['height']),'rx':'8','fill':zone.get('fill','#F4F7FB'),'stroke':'#8395AA','stroke-dasharray':'6 4'})
        text(root,zone['label'],zone['x']+12,zone['y']+20,12,'start')
    for frame in model.get('frames',[]):
        ET.SubElement(root,'rect',{'x':str(frame['x']),'y':str(frame['y']),'width':str(frame['width']),'height':str(frame['height']),'fill':'none','stroke':'#8395AA'})
        text(root,frame['label'],frame['x']+8,frame['y']+16,11,'start')
    for n in model['nodes']:
        x,y,wid,hei=n['x'],n['y'],n['width'],n['height'];kind=n['kind']
        g=ET.SubElement(root,'g',{'data-node-id':n['id']})
        if kind in ('start','end','initial','final','timer'):
            fill='#172B4D' if kind=='initial' else '#FFFFFF';cx,cy=x+wid/2,y+hei/2
            ET.SubElement(g,'ellipse',{'cx':str(cx),'cy':str(cy),'rx':str(wid/2-2),'ry':str(hei/2-2),'fill':fill,'stroke':'#344563','stroke-width':'3' if kind in ('end','final') else '1.7'})
            if kind=='final':ET.SubElement(g,'ellipse',{'cx':str(cx),'cy':str(cy),'rx':str(wid/2-7),'ry':str(hei/2-7),'fill':'#172B4D'})
            if kind=='timer':
                ET.SubElement(g,'line',{'x1':str(cx),'y1':str(cy),'x2':str(cx),'y2':str(cy-8),'stroke':'#344563'})
                ET.SubElement(g,'line',{'x1':str(cx),'y1':str(cy),'x2':str(cx+6),'y2':str(cy+3),'stroke':'#344563'})
            if n['label']:
                lx,ly=n.get('label_position',[cx,y+hei+15]);text(g,n['label'],lx,ly,10)
        elif kind=='xor':
            ET.SubElement(g,'polygon',{'points':f'{x+wid/2},{y} {x+wid},{y+hei/2} {x+wid/2},{y+hei} {x},{y+hei/2}','fill':'#FFF7D6','stroke':'#344563'})
            text(g,'X',x+wid/2,y+hei/2+5,16);text(g,n['label'],x+wid/2,y-8,10)
        else:
            ET.SubElement(g,'rect',{'x':str(x),'y':str(y),'width':str(wid),'height':str(hei),'rx':'8' if kind!='entity' else '0','fill':n.get('fill','#EAF1FF'),'stroke':'#344563','stroke-width':'1.5'})
            text(g,n['label'],x+wid/2,y+hei/2-(len(n['label'].split('\n'))-1)*7+4,12)
        if model['family']=='sequence':ET.SubElement(g,'line',{'x1':str(x+wid/2),'x2':str(x+wid/2),'y1':str(y+hei),'y2':str(model['canvas'][1]-85),'stroke':'#8395AA','stroke-dasharray':'5 4'})
    for edge in model['edges']:
        pp=points(model,edge);attrs={'points':' '.join(f'{x},{y}' for x,y in pp),'fill':'none','stroke':'#42526E','stroke-width':'1.5','data-edge-id':edge['id']}
        if edge['kind'] in ('message','return'):attrs['stroke-dasharray']='6 4'
        ET.SubElement(root,'polyline',attrs)
        tx,ty=pp[-1];px,py=pp[-2];length=math.hypot(tx-px,ty-py);require(length>0,'zero length terminal segment')
        ux,uy=(tx-px)/length,(ty-py)/length
        left=(tx-9*ux+4*uy,ty-9*uy-4*ux);right=(tx-9*ux-4*uy,ty-9*uy+4*ux)
        open_head=edge['kind'] in ('message','return')
        ET.SubElement(root,'polyline' if open_head else 'polygon',{'points':f'{left[0]},{left[1]} {tx},{ty} {right[0]},{right[1]}','fill':'none' if open_head else '#42526E','stroke':'#42526E','stroke-width':'1.5','data-arrow-for':edge['id']})
        if model['family']=='bpmn' and edge['kind']=='message':ET.SubElement(root,'circle',{'cx':str(pp[0][0]),'cy':str(pp[0][1]),'r':'3','fill':'#FFFFFF','stroke':'#42526E'})
        default_y=(pp[0][1]+pp[-1][1])/2-8
        if model['family']!='sequence':
            nodes={n['id']:n for n in model['nodes']};a,b=nodes[edge['source']],nodes[edge['target']]
            if abs(a['y']-b['y'])<=5:default_y=min(a['y'],b['y'])-12
        x,y=edge.get('label_position',[(pp[0][0]+pp[-1][0])/2,default_y]);text(root,edge['label'],x,y,10)
    text(root,model['legend'],24,model['canvas'][1]-36,10,'start','#586B82')
    text(root,'Example only; not deployed configuration or executable process certification.',24,model['canvas'][1]-18,10,'start','#586B82')
    return ET.tostring(root,encoding='unicode')+'\n'


def drawio(model):
    validate(model);root=ET.Element('mxfile',{'host':'offline-workflow','version':'1.0','type':'device'});diagram=ET.SubElement(root,'diagram',{'id':model['id'],'name':model['title']});graph=ET.SubElement(diagram,'mxGraphModel',{'pageWidth':str(model['canvas'][0]),'pageHeight':str(model['canvas'][1])});cells=ET.SubElement(graph,'root');ET.SubElement(cells,'mxCell',{'id':'0'});ET.SubElement(cells,'mxCell',{'id':'1','parent':'0'})
    for z in model['zones']:
        c=ET.SubElement(cells,'mxCell',{'id':z['id'],'value':z['label'],'vertex':'1','parent':'1','style':'swimlane;html=0;startSize=26;fillColor=#F4F7FB;dashed=1;'});ET.SubElement(c,'mxGeometry',{'x':str(z['x']),'y':str(z['y']),'width':str(z['width']),'height':str(z['height']),'as':'geometry'})
    zones={z['id']:z for z in model['zones']}
    for n in model['nodes']:
        z=zones.get(n['zone'],{'x':0,'y':0});shape='rhombus' if n['kind']=='xor' else 'ellipse' if n['kind'] in ('start','end','initial','final','timer') else 'rectangle'
        height=model['canvas'][1]-n['y']-85 if model['family']=='sequence' else n['height']
        style=f'shape={shape};rounded=1;whiteSpace=wrap;html=0;fillColor=#EAF1FF;'
        if model['family']=='sequence':style=f'shape=umlLifeline;perimeter=lifelinePerimeter;html=0;size={n["height"]};container=1;collapsible=0;'
        c=ET.SubElement(cells,'mxCell',{'id':n['id'],'value':n['label'],'vertex':'1','parent':n['zone'] or '1','style':style});ET.SubElement(c,'mxGeometry',{'x':str(n['x']-z['x']),'y':str(n['y']-z['y']),'width':str(n['width']),'height':str(height),'as':'geometry'})
    for e in model['edges']:
        style='endArrow=block;html=0;'+('dashed=1;' if e['kind'] in ('message','return') else '')
        if model['family']=='sequence':
            nodes={n['id']:n for n in model['nodes']};a,b=nodes[e['source']],nodes[e['target']]
            sy=(e['y']-a['y'])/(model['canvas'][1]-a['y']-85);ty=(e['y']-b['y'])/(model['canvas'][1]-b['y']-85)
            style+=f'exitX=0.5;exitY={sy};entryX=0.5;entryY={ty};exitPerimeter=0;entryPerimeter=0;'
        c=ET.SubElement(cells,'mxCell',{'id':e['id'],'value':e['label'],'edge':'1','parent':'1','source':e['source'],'target':e['target'],'style':style});geo=ET.SubElement(c,'mxGeometry',{'relative':'1','as':'geometry'})
        if e.get('points'):
            array=ET.SubElement(geo,'Array',{'as':'points'})
            for x,y in e['points'][1:-1]:ET.SubElement(array,'mxPoint',{'x':str(x),'y':str(y)})
    return ET.tostring(root,encoding='unicode')+'\n'


def bpmn(model):
    validate(model);require(model['family']=='bpmn','BPMN model required')
    for prefix,url in [('bpmn',BPMN),('bpmndi',BPMNDI),('dc',DC),('di',DI)]:ET.register_namespace(prefix,url)
    root=ET.Element('{'+BPMN+'}definitions',{'id':'definitions_'+model['id'],'targetNamespace':'https://example.invalid/workflow-diagrams'})
    nodes={n['id']:n for n in model['nodes']};processes={};tag={'start':'startEvent','end':'endEvent','task':'task','send':'sendTask','receive':'receiveTask','xor':'exclusiveGateway','timer':'boundaryEvent'}
    for zone in model['zones']:
        proc=ET.SubElement(root,'{'+BPMN+'}process',{'id':'process_'+zone['id'],'isExecutable':'false'});processes[zone['id']]=proc
        for n in model['nodes']:
            if n['zone']!=zone['id']:continue
            attrs={'id':n['id'],'name':n['label']}
            if n['kind']=='timer':attrs.update(attachedToRef=n['attached_to'],cancelActivity='true')
            defaults=[e['id'] for e in model['edges'] if e['source']==n['id'] and e.get('default')]
            if defaults:attrs['default']=defaults[0]
            element=ET.SubElement(proc,'{'+BPMN+'}'+tag[n['kind']],attrs)
            for direction,key in [('incoming','target'),('outgoing','source')]:
                for e in model['edges']:
                    if e['kind']=='sequence' and e[key]==n['id']:ET.SubElement(element,'{'+BPMN+'}'+direction).text=e['id']
            if n['kind']=='timer':
                timer=ET.SubElement(element,'{'+BPMN+'}timerEventDefinition');ET.SubElement(timer,'{'+BPMN+'}timeDuration').text='PT24H'
        for e in model['edges']:
            if e['kind']=='sequence' and nodes[e['source']]['zone']==zone['id']:
                el=ET.SubElement(proc,'{'+BPMN+'}sequenceFlow',{'id':e['id'],'name':e['label'],'sourceRef':e['source'],'targetRef':e['target']})
                if e.get('condition'):ET.SubElement(el,'{'+BPMN+'}conditionExpression',{'{http://www.w3.org/2001/XMLSchema-instance}type':'bpmn:tFormalExpression'}).text=e['condition']
    collab=ET.SubElement(root,'{'+BPMN+'}collaboration',{'id':'collaboration_'+model['id']})
    for z in model['zones']:ET.SubElement(collab,'{'+BPMN+'}participant',{'id':z['id'],'name':z['label'],'processRef':'process_'+z['id']})
    for e in model['edges']:
        if e['kind']=='message':ET.SubElement(collab,'{'+BPMN+'}messageFlow',{'id':e['id'],'name':e['label'],'sourceRef':e['source'],'targetRef':e['target']})
    dia=ET.SubElement(root,'{'+BPMNDI+'}BPMNDiagram',{'id':'diagram_'+model['id']});plane=ET.SubElement(dia,'{'+BPMNDI+'}BPMNPlane',{'id':'plane_'+model['id'],'bpmnElement':'collaboration_'+model['id']})
    for n in model['zones']+model['nodes']:
        shape=ET.SubElement(plane,'{'+BPMNDI+'}BPMNShape',{'id':'shape_'+n['id'],'bpmnElement':n['id'],'isHorizontal':'true'});ET.SubElement(shape,'{'+DC+'}Bounds',{k:str(n[k]) for k in ('x','y','width','height')})
    for e in model['edges']:
        edge=ET.SubElement(plane,'{'+BPMNDI+'}BPMNEdge',{'id':'di_'+e['id'],'bpmnElement':e['id']})
        for x,y in points(model,e):ET.SubElement(edge,'{'+DI+'}waypoint',{'x':str(x),'y':str(y)})
    return ET.tostring(root,encoding='unicode')+'\n'


def catalog():
    c=load(LIBRARY/'index.json');require(c['schema_version']==1,'unsupported catalog')
    ids=set()
    for row in c['templates']:
        identifier(row['id']);require(row['id'] not in ids,'duplicate catalog id');ids.add(row['id'])
        require(contained(LIBRARY,row['source']).is_file(),'missing catalog source')
    return c


def check():
    c=catalog();counts={'templates':0,'exports':0}
    sources=load(LIBRARY/'sources.json')
    source_ids={s['id'] for s in sources['sources']}
    require(len(source_ids)==len(sources['sources']),'duplicate source id')
    for source in sources['sources']:
        require(source.get('license') and source.get('checked_at') and source.get('recheck_conditions'),'source provenance incomplete')
        require(re.fullmatch('[0-9a-f]{40}',source['reference_commit']),'unpinned source')
    for row in c['templates']:
        m=validate(load(contained(LIBRARY,row['source'])));require(m['id']==row['id'],'catalog/model mismatch')
        require(row['source_ids'] and all(x in source_ids for x in row['source_ids']),'unknown template source')
        for extension,fn in [('svg',svg),('drawio',drawio)]+([('bpmn',bpmn)] if m['family']=='bpmn' else []):
            p=contained(LIBRARY,f"exports/{m['id']}.{extension}");actual=p.read_text();require(actual==fn(m),'stale export')
            parsed=ET.fromstring(actual);require(not any(x.tag.split('}')[-1] in ('script','foreignObject','image') for x in parsed.iter()),'active or external SVG content')
            require(not any('href' in k or k.lower().startswith('on') for x in parsed.iter() for k in x.attrib),'active export attribute')
            counts['exports']+=1
        counts['templates']+=1
    return {'passed':True,**counts,'scope':'catalog, model invariants, exact original SVG/draw.io/BPMN exports; not third-party renderer or full notation certification'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    lookup=sub.add_parser('lookup');lookup.add_argument('family');lookup.add_argument('--limit',type=int,default=5)
    read=sub.add_parser('read');read.add_argument('id')
    sub.add_parser('check')
    export=sub.add_parser('export');export.add_argument('id');export.add_argument('--format',choices=('svg','drawio','bpmn'),required=True);export.add_argument('--out',type=Path,required=True)
    a=p.parse_args(argv)
    if a.cmd=='check':return check()
    c=catalog()
    if a.cmd=='lookup':
        require(1<=a.limit<=10,'limit must be 1..10');rows=[r for r in c['templates'] if a.family==r['family'] or a.family in r['topics']];return {'matches':rows[:a.limit],'more':len(rows)>a.limit}
    rows=[r for r in c['templates'] if r['id']==a.id];require(len(rows)==1,'template not found')
    m=validate(load(contained(LIBRARY,rows[0]['source'])))
    if a.cmd=='read':return m
    require(not a.out.exists() and not a.out.is_symlink(),'export destination already exists')
    require(a.out.suffix=='.'+a.format,'export suffix mismatch')
    a.out.write_text({'svg':svg,'drawio':drawio,'bpmn':bpmn}[a.format](m))
    return {'exported':a.out.name,'format':a.format,'engine':'original offline exporter'}


if __name__=='__main__':
    try:print(json.dumps(main(),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,ET.ParseError):
        print('diagram_library: invalid model/catalog/export; input withheld',file=sys.stderr);sys.exit(2)
