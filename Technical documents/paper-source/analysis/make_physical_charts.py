#!/usr/bin/env python3
"""Retypeset the original Figure 6 at its printed size; all historical counts unchanged."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures/charts'
p = json.loads((ROOT / 'data/physical_labeled_results.json').read_text())['prototype']
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':8.5, 'axes.titlesize':9, 'axes.labelsize':8.5})
fig, ax = plt.subplots(figsize=(3.5,2.05))
n = p['common_assessed_pairs']['n']
vals = [p['derived_common_pair_events'][m] / n * 100 for m in ['OFF','ON']]
ax.plot([0,1], vals, marker='o', lw=1.7, color='#167c80', markersize=5)
for i, m in enumerate(['OFF','ON']):
 ax.annotate(f"{p['derived_common_pair_events'][m]}/{n}", (i,vals[i]), xytext=(10,0) if i == 0 else (-10,8), textcoords='offset points', ha='left' if i == 0 else 'right', fontsize=9, fontweight='bold')
ax.set_xticks([0,1], ['Guard OFF','Guard ON'])
ax.set_ylim(0,105); ax.set_xlim(-.07,1.07)
ax.set_ylabel('Attack-target output (%)')
ax.set_title(f'Same-photo pairs (n = {n})')
ax.grid(axis='y',alpha=.2)
fig.tight_layout(pad=.7); fig.savefig(OUT/'physical_paired.pdf',bbox_inches='tight');plt.close(fig)
records = [p['modes'][m][k] for k in ['attack_target_output','correct_parameter'] for m in ['OFF','ON']]
a = [r['assessed'] for r in records]; b = [r['pending'] for r in records]
fig,ax = plt.subplots(figsize=(3.5,2.05));x=np.arange(4)
ax.bar(x,a,label='Assessed',color='#167c80',width=.65)
ax.bar(x,b,bottom=a,label='Pending',color='#c6cbd0',width=.65)
for i,(v,w) in enumerate(zip(a,b)):ax.text(i,v+w+.5,f'{v}+{w}',ha='center',fontsize=8)
ax.set_ylim(0,33);ax.set_ylabel('Eligible cases')
ax.set_xticks(x,['OFF\nattack','ON\nattack','OFF\nvalue','ON\nvalue'])
ax.tick_params(axis='x',length=0,labelsize=8)
ax.grid(axis='y',alpha=.15)
ax.set_axisbelow(True)
fig.suptitle('Physical endpoint coverage',fontsize=9,y=.99)
fig.legend(loc='upper center',bbox_to_anchor=(.58,.91),ncol=2,frameon=False,fontsize=7.8,columnspacing=.8,handlelength=1.2)
fig.subplots_adjust(left=.16,bottom=.22,right=.98,top=.70)
fig.savefig(OUT/'physical_coverage.pdf',bbox_inches='tight');plt.close(fig)
