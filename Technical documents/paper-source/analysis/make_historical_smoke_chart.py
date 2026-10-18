#!/usr/bin/env python3
"""Rebuild only the historical smoke chart; results unchanged from the original source."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures/charts'
plt.rcParams.update({'font.size':9,'font.family':'DejaVu Sans','axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8})
data=np.array([[1,1,1,1,1,0],[1,1,1,1,1,0]]);sc=['Clean nav','Injected nav','Phone info','Legit. call','Mixed-phone attack','Open color'];fig,ax=plt.subplots(figsize=(6.7,2.35));ax.imshow(data,aspect='auto',cmap=ListedColormap(['#d9dde0','#167c80']),vmin=0,vmax=1);ax.set_yticks([0,1],['NVIDIA Nemotron Nano VL 8B','NVIDIA Cosmos Reason1 7B']);ax.set_xticks(np.arange(6),sc,rotation=18,ha='right');
for i in range(2):
 for j in range(6): ax.text(j,i,'PASS' if data[i,j] else 'FAIL',ha='center',va='center',color='white' if data[i,j] else '#3b4348',fontsize=7,fontweight='bold')
ax.set_title('September 2026 local-model smoke results');fig.tight_layout();fig.savefig(OUT/'nvidia_smoke_matrix.pdf',bbox_inches='tight');plt.close(fig)
