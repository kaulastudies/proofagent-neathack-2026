"""Render a captioned evidence walkthrough using actual project artifacts.

This is a silent artifact walkthrough, not a recording of interactive execution.
"""
import json
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
FRAMES=ROOT/'artifacts/demo-frames'
FRAMES.mkdir(parents=True,exist_ok=True)
subprocess.run(['pdftoppm','-f','1','-singlefile','-scale-to','1800','-png',
    str(ROOT/'docs/cfo/ProofAgent_Business_Plan_Updated.pdf'),str(FRAMES/'cfo-page-1')],check=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
BG='#08131f'; FG='#eff5fc'; MUTED='#b2c0d2'; ACCENT='#70e1c7'
def font(size,bold=False,mono=False):
    return ImageFont.truetype(MONO if mono else BOLD if bold else FONT,size)
def wrap(draw,text,x,y,width,size=28,color=FG):
    words=text.split();lines=[];line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if draw.textlength(candidate,font=font(size))>width and line:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    for line in lines:
        draw.text((x,y),line,font=font(size),fill=color);y+=size+12
    return y

def scene(number,title,label,bullets,duration,picture=None,panel=None,source='Public repository evidence'):
    im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
    d.text((70,42),'AI EVALUATION LAB  /  NEATHACK 2026',font=font(21,True),fill=ACCENT)
    d.text((70,88),title,font=font(48,True),fill=FG)
    d.text((70,153),label,font=font(23),fill=MUTED)
    width=505 if picture or panel else 1500;y=245
    for bullet in bullets:
        d.ellipse((70,y+10,80,y+20),fill=ACCENT)
        y=wrap(d,bullet,100,y,width-30,size=29)+35
    if picture:
        pic=Image.open(picture).convert('RGB');pic.thumbnail((1190,810),Image.Resampling.LANCZOS)
        x=650+(1190-pic.width)//2;py=205+(810-pic.height)//2
        d.rounded_rectangle((x-10,py-10,x+pic.width+10,py+pic.height+10),radius=12,fill='#1c2d40')
        im.paste(pic,(x,py))
    if panel:
        d.rounded_rectangle((650,235,1835,940),radius=20,fill='#152638',outline='#354b61',width=2)
        y=280
        for line in panel:
            for part in textwrap.wrap(line,width=57,replace_whitespace=False,drop_whitespace=False) or ['']:
                d.text((690,y),part,font=font(28,mono=True),fill=ACCENT if ('PASS' in part or '748' in part) else FG)
                y+=44
    d.line((70,1018,1840,1018),fill='#294258',width=2)
    d.text((70,1031),source,font=font(20),fill=MUTED)
    d.text((1750,1031),f'{number:02d} / 09',font=font(20),fill=ACCENT)
    path=FRAMES/f'{number:02d}.png';im.save(path)
    return path,duration

report=json.loads((ROOT/'artifacts/neatlogs/live-tax-verified.json').read_text())
a=report['attempts'][0];u=a['model_usage']
scenes=[
 scene(1,'ProofAgent: prove the repair','CAPTIONED EVIDENCE WALKTHROUGH — ACTUAL ARTIFACTS',[
 'An agent proposes a repair. Independent acceptance tests decide whether it worked.',
 'A bounded billing-repair prototype with live Claude inference, trace evidence and checkpoint recovery.',
 'Rama Chandra / AI Evaluation Lab. Event code and reproducible evidence are public.'
 ],10,panel=['GOAL','Discount before tax','TOOLS','Restricted arithmetic patch','Independent Python acceptance tests','STATE','Atomic checkpoint + source hashes','RULE','A proposal is not a success']),
 scene(2,'The task: discount before tax','TRUSTED FIXTURE — FAILING BASELINE',[
 'The buggy expression taxes the full subtotal, then subtracts the discount.',
 'For subtotal 100, discount 20 and tax 10%, the expected total is 88.',
 'Four independent acceptance tests cover discount order, full discount, no discount and zero tax.'
 ],18,panel=['Before:','subtotal * (1 + tax_rate) - discount','','Baseline: 2 tests fail / 4 tests','','After proposed expression:','(subtotal - discount) * (1 + tax_rate)','','Acceptance tests remain unchanged.'],source='Source: fixtures/tax_order + actual live report'),
 scene(3,'A real integration failure','NEATLOGS BEFORE — ACTUAL LIVE CLAUDE CALL',[
 'Claude returned the correct arithmetic expression in a JSON code block.',
 'Our bare-JSON parser rejected the formatting. No patch was applied.',
 'Neatlogs captured the error and the model output: 3 spans, 779 tokens, about 11.4 seconds.'
 ],18,picture=ROOT/'artifacts/neatlogs/live-before.jpg',source='Actual trace: 07d3ad61935978f8d194a239a3708a15'),
 scene(4,'Fix formatting; keep the verifier','NEATLOGS AFTER — ACTUAL LIVE CLAUDE CALL',[
 'Accept plain JSON or one complete JSON fence. Reject surrounding prose and extra fields.',
 'The new proposal passed all 4 unchanged tax acceptance tests.',
 f"Verified first attempt. {u['total_tokens']} tokens; {u['latency_ms']/1000:.3f}s model latency. Dollar cost not measured."
 ],18,picture=ROOT/'artifacts/neatlogs/live-after.jpg',source='Actual trace: d70e80a1d53f145dec4d26dc8d947200'),
 scene(5,'Success is an evidence gate','IMPLEMENTED LIMITS — NOT A GENERAL CODE SANDBOX',[
 'Model output is data: only allowed arithmetic syntax and variables reach the patch tool.',
 'At most 3 candidate attempts; 384 output tokens per gateway call; SDK auto-retries disabled.',
 'Frozen acceptance files, patch hashes and fresh subprocess tests gate the result. Original fixture preserved.'
 ],15,panel=['Actual runtime result:','verdict: VERIFIED_PASS','model: claude-haiku','accepted: discount-before-tax repair','files_unchanged_except_patch: true','original_unchanged: true','','No generated shell commands.','Only bundled trusted Python fixtures.'],source='Source: artifacts/neatlogs/live-tax-verified.json'),
 scene(6,'Recover without a false success','OFFLINE REPLAY / REAL PROCESS AND ACCEPTANCE TESTS',[
 'A separate regression starts a process, saves a failed candidate, exits 75, then resumes in a new process.',
 'The saved attempt is preserved and the next proposal is independently checked.',
 'Completed successful checkpoints are re-tested on resume. Edited success expressions fail verification.'
 ],16,panel=['Interrupt process: exit 75','state: RUNNING','attempt 1: VERIFIED_FAIL','','Resume new process: exit 0','attempt 1 preserved','attempt 2: VERIFIED_PASS','','27 regression tests pass locally.'],source='Source: tests/test_resumable_agent.py — scripted proposals'),
 scene(7,'Entire guides the change','GENUINE ENTIRE GRAPH USE — DEVELOPMENT EVIDENCE',[
 'Entire Graph search located verification-related code. Impact analysis identified the CLI, demo and test callers.',
 'The completed-checkpoint fix was checked against those callers.',
 'Graph verification recorded a failing regression baseline and passing result. Its unittest verdict is exit-code-only.'
 ],16,panel=['Entire CLI 0.11.4','Entire Graph v0.4.0','','search -> inspect -> impact -> repair','','Baseline regression: exit 1','After repair: exit 0','','No session checkpoint is claimed.'],source='Source: artifacts/entire/ — original vendor outputs'),
 scene(8,'cfo.ai plans the business','ORIGINAL CFO.AI EXPORT — ALL FORECASTS HYPOTHETICAL',[
 'Six-month pricing, delivery costs, adoption, break-even and cash movement scenarios.',
 'Independent arithmetic review reproduces the export. Base Month 6: $3,230 revenue; $2,046 recurring cost.',
 'No customers or revenue confirmed. Opening cash and runway uncalculated. AWS allowance received but unapplied.'
 ],18,picture=FRAMES/'cfo-page-1.png',source='Source: original cfo.ai PDF + verify_business_plan.py'),
 scene(9,'Verify before trusting the verdict','PUBLIC CODE + INSPECTABLE SPONSOR EVIDENCE',[
 'neatlogs: live before/after traces. Entire: repository analysis. cfo.ai: exported business plan.',
 'Current scope: three trusted billing fixtures; one live tax-repair case; separately labeled scripted rejection and process recovery.',
 'Prototype limits: unsigned local state, one process per state file, no arbitrary customer-code execution.',
 'github.com/kaulastudies/proofagent-neathack-2026'
 ],12,source='ProofAgent / AI Evaluation Lab / October 12, 2026')
]
(ROOT/'artifacts/demo-scenes.json').write_text(json.dumps([{'scene':i+1,'seconds':secs,'frame':p.name} for i,(p,secs) in enumerate(scenes)],indent=2)+'\n')
playlist=FRAMES/'frames.ffconcat'
with playlist.open('w') as f:
    f.write('ffconcat version 1.0\n')
    for p,secs in scenes:f.write(f"file '{p.as_posix()}'\nduration {secs}\n")
    f.write(f"file '{scenes[-1][0].as_posix()}'\n")
output=ROOT.parent/'output/ProofAgent_neatHack_demo.mp4'
output.parent.mkdir(exist_ok=True)
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(playlist),
    '-filter_threads','1','-vf','fps=15,format=yuv420p','-c:v','libx264','-threads','2','-preset','veryfast','-crf','20','-t',str(sum(s for _,s in scenes)),
    '-movflags','+faststart',str(output)],check=True)
print('Rendered',sum(s for _,s in scenes),'second silent evidence walkthrough:',output)
