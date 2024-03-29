# -*- coding: utf-8 -*-
"""
Created on Mon Jun 7 15:36:24 2021

@author: Maria
"""
import time
import datetime
import pickle
import itertools
import numpy as np
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
from funcs import pic_to_ar
from funcs import attrs
from funcs import un_roll
from funcs import coact
from funcs import coact_sh
from funcs import coact40
from SER import SERmodel_multneuro
import bct 

start_time = time.time()

#%% get an array of all the possible network states
states = list(itertools.product([0, 1, -1], repeat=12))
states_ar = np.array(states)

# FoG healthy matrix
A1 = np.array(
    [
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
        [1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0],
        [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1],
        [0, -1, -1, -1, 0, 0, 0, 0, -1, 0, -1, -1],
        [0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1],
        [0, -1, 0, -1, -1, -1, 0, -1, -1, 0, -1, -1],
        [0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, 0],
        [0, 0, 0, 0, -1, 0, -1, -1, -1, 0, -1, 0],
        [0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, -1, 1, -1, -1, -1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
    ]
)  # directed FOG network
# (LC,PRF,CNF,PPN,SNr,STN,GPi,GPe,Str,Ctx,SNc,Th)

#The matrix used for a random null test
# A1 = np.array([[ 0,  0,  1,  0,  0,  1,  0,  0,  1,  0,  0,  1],
#        [ 0,  0,  0,  0,  1,  1,  0,  1,  0,  1,  1,  0],
#        [ 0,  1,  0,  1,  0,  0,  0,  0,  0,  1,  0,  1],
#        [ 1,  1,  1,  0,  1,  1,  1,  0,  1,  1,  1,  0],
#        [ 0,  0, -1,  0,  0, -1, -1, -1, -1,  0, -1,  0],
#        [ 1,  1,  0,  0,  1,  0,  1,  1,  1,  1,  1,  0],
#        [ 0, -1,  0, -1, -1,  0,  0, -1, -1, -1, -1, -1],
#        [ 0,  0,  0,  0, -1, -1, -1, -1, -1,  0, -1, -1],
#        [ 0,  0,  0, -1, -1,  0,  0, -1, -1,  0, -1,  0],
#        [ 0,  1,  0,  1,  1,  0,  0,  1,  0,  1,  1,  1],
#        [ 0, -1,  0,  1, -1,  0, -1,  0, -1,  0,  0,  0],
#        [ 0,  1,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0]])

#A1 = bct.randmio_dir_signed(A1,itr=5)[0] #to generate a randomize matrix

# FoG PD matrix
A2 = np.array(
    [
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
        [1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0],
        [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1],
        [0, -1, -1, -1, 0, 0, 0, 0, -1, 0, -1, -1],
        [0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1],
        [0, -1, 0, -1, -1, -1, 0, -1, -1, 0, -1, -1],
        [0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, 0],
        [0, 0, 0, 0, -1, 0, -1, -1, -1, 0, -1, 0],
        [0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
    ]
)  # directed FOG network
# (LC,PRF,CNF,PPN,SNr,STN,GPi,GPe,Str,Ctx,SNc,Th)

T = 100  # time
NN = 1  # number of neurons

# parameters for the determenistic version of SER
sp = 0
refr = 1

#%% create file and run ser for all states

name = f'Files/data_h_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file = open(name, "wb")

# to change the matrix for STN-DBS
FOG_directed_stn = A2.astype(np.float32)
FOG_directed_stn[5, :] = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]  # all connections from stn are lesioned
adj_stn = FOG_directed_stn.T
STN = states_ar[states_ar[:, 5] == -1]  # stn always refractory inits

## change matrix to get STN+SNr-DBS
FOG_directed_ssnr = A2.astype(np.float32)
FOG_directed_ssnr[5, :] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
FOG_directed_ssnr[4, :] = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]  # all connections from snr are lesioned
adj_ssnr = FOG_directed_ssnr.T
SSNR = STN[STN[:, 4] == -1]  # ssnr is refractory

for i in range(len(states)):
    ## simulate all types
    res_h = SERmodel_multneuro(
        NN, A1.T, T, sp, refr, np.array(states[i])
    )  # results for healthy state directed graph/no dbs
    datalist = [res_h]

    ##write into a file
    pickle.dump(datalist, file)

file.close()

# new file for PD
name1 = f'Files/data_pd_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file1 = open(name1, "wb")

for i in range(len(states)):
    ## simulate all types
    res_pd = SERmodel_multneuro(
        NN, A2.T, T, sp, refr, np.array(states[i])
    )  # results for PD state directed graph/no dbs
    datalist = [res_pd]

    ##write into a file
    pickle.dump(datalist, file1)

file1.close()

# new file for STN-DBS
name2 = f'Files/data_stn_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file2 = open(name2, "wb")

for i in range(len(states)):
    ## simulate all types
    res_stn_on = SERmodel_multneuro(
        NN, adj_stn, T, sp, refr, np.array(states[i])
    )  # results for STN state directed graph
    datalist = [res_stn_on]

    ##write into a file
    pickle.dump(datalist, file2)

file2.close()

# new file for STN+SNr-DBS
name3 = f'Files/data_ssnr_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file3 = open(name3, "wb")

for i in range(len(states)):
    ## simulate all types
    res_ssnr_on = SERmodel_multneuro(
        NN, adj_ssnr, T, sp, refr, np.array(states[i])
    )  # results for ssnr state directed graph
    datalist = [res_ssnr_on]

    ##write into a file
    pickle.dump(datalist, file3)

file3.close()

#%% pickled data postprocessing
# convert to arrays
h = pic_to_ar(name)
pd = pic_to_ar(name1)
stn = pic_to_ar(name2)
ssnr = pic_to_ar(name3)

# calculate attractors
attrs_h = attrs(h)
attrs_pd = attrs(pd)
attrs_stn = attrs(stn)
attrs_ssnr = attrs(ssnr)

h_sp, h_c, indd_h = un_roll(attrs_h)
pd_sp, pd_c, indd_pd = un_roll(attrs_pd)
stn_sp, stn_c, indd_stn = un_roll(attrs_stn)
ssnr_sp, ssnr_c, indd_ssnr = un_roll(attrs_ssnr)

# new file for healthy attractors
name_at = (
    f'Files/attractors_h_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
)
file_at = open(name_at, "wb")

pickle.dump(attrs_h, file_at)

file_at.close()

# new file for pd attractors
name_at1 = (
    f'Files/attractors_pd_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
)
file_at1 = open(name_at1, "wb")

pickle.dump(attrs_pd, file_at1)

file_at1.close()

# new file for stn attractors
name_at2 = (
    f'Files/attractors_stn_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
)
file_at2 = open(name_at2, "wb")

pickle.dump(attrs_stn, file_at2)

file_at2.close()

# new file for ssnr attractors
name_at3 = (
    f'Files/attractors_ssnr_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
)
file_at3 = open(name_at3, "wb")

pickle.dump(attrs_ssnr, file_at3)

file_at3.close()

# attr h
name_sp = f'Files/space_h_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_sp = open(name_sp, "wb")

name_c = f'Files/counts_h_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_c = open(name_c, "wb")

pickle.dump([h_sp], file_sp)
pickle.dump([h_c], file_c)

file_c.close()
file_sp.close()

# attr pd
name_sp1 = f'Files/space_pd_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_sp1 = open(name_sp1, "wb")

name_c1 = f'Files/counts_pd_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_c1 = open(name_c1, "wb")

pickle.dump([pd_sp], file_sp1)
pickle.dump([pd_c], file_c1)

file_c1.close()
file_sp1.close()

# attr stn
name_sp2 = f'Files/space_stn_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_sp2 = open(name_sp2, "wb")

name_c2 = f'Files/counts_stn_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_c2 = open(name_c2, "wb")

pickle.dump([stn_sp], file_sp2)
pickle.dump([stn_c], file_c2)

file_c2.close()
file_sp2.close()

# attr ssnr
name_sp3 = f'Files/space_ssnr_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_sp3 = open(name_sp2, "wb")

name_c3 = f'Files/counts_ssnr_{datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")}.pckl'
file_c3 = open(name_c3, "wb")

pickle.dump([ssnr_sp], file_sp3)
pickle.dump([ssnr_c], file_c3)

file_c3.close()
file_sp3.close()

#%% check if one set of attractors is included in another
# to analyse ssnr attractor space please use attractor_space_ssnr instead of
# attractor_space_stn, the same goes to attractor_counts_ssnr

attractor_space_h = h_sp
attractor_space_pd = pd_sp
attractor_counts_h = h_c
attractor_counts_pd = pd_c
attractor_space_stn = stn_sp
attractor_counts_stn = stn_c
attractor_space_ssnr = ssnr_sp
attractor_counts_ssnr = ssnr_c

now_dbs = attractor_space_ssnr
now_dbs_counts = attractor_counts_ssnr

counter = 0
overlap = np.array([])
overlap1 = np.array([])
ind_j = np.array([])
ind_h = np.array([])
for i in range(len(attractor_space_h)):
    for j in range(len(attractor_space_pd)):
        if np.sum(attractor_space_h[i] == attractor_space_pd[j]) == 36:
            counter += 1
            overlap = np.append(overlap, attractor_counts_h[i])
            overlap1 = np.append(overlap1, attractor_counts_pd[j])
            ind_j = np.append(ind_j, j)
            ind_h = np.append(ind_h, i)

print("--------stn/h")
# to analyse ssnr attractor space please use attractor_space_ssnr instead of
# attractor_space_stn, the same goes to attractor_counts_ssnr

counter1 = 0
overlap2 = np.array([])
overlap3 = np.array([])
compare_h = attractor_space_h
compare_stn = now_dbs
ind_stn = np.array([])
for i in range(len(compare_h)):
    for j in range(len(compare_stn)):
        if np.sum(compare_h[i] == compare_stn[j]) == 36:
            counter1 += 1
            overlap2 = np.append(overlap2, attractor_counts_h[i])
            overlap3 = np.append(overlap3, now_dbs_counts[j])
            ind_stn = np.append(ind_stn, j)

print("--------stn/pd")
# to analyse ssnr attractor space please use attractor_space_ssnr instead of
# attractor_space_stn, the same goes to attractor_counts_ssnr

counter2 = 0
overlap4 = np.array([])
overlap5 = np.array([])
compare_pd = attractor_space_pd
ind_i = np.array([])

for i in range(len(compare_pd)):
    for j in range(len(compare_stn)):
        if np.sum(compare_pd[i] == compare_stn[j]) == 36:
            counter2 += 1
            overlap4 = np.append(overlap4, attractor_counts_pd[i])
            overlap5 = np.append(overlap5, now_dbs_counts[j])
            ind_i = np.append(ind_i, j)

# calculate the intersection of sets
counter3 = 0
overlap6 = np.array([])
overlap7 = np.array([])
overlap8 = np.array([])

for i in range(len(attractor_space_pd)):
    for j in range(len(attractor_space_h)):
        if np.sum(attractor_space_pd[i] == attractor_space_h[j]) == 36:
            for k in range(len(compare_stn)):
                if np.sum(compare_pd[i] == compare_stn[k]) == 36:
                    counter3 += 1
                    overlap6 = np.append(overlap6, attractor_counts_pd[i])
                    overlap7 = np.append(overlap7, attractor_counts_h[j])
                    overlap8 = np.append(overlap8, now_dbs_counts[k])

# calculate capacity of intersects
all_ands = counter3
h_and_pd_notall = counter - all_ands
h_and_stn_notall = counter1 - all_ands
pd_and_stn_notall = counter2 - all_ands
h_notall = len(attractor_space_h) - counter - counter1 + all_ands
pd_notall = len(attractor_space_pd) - counter - counter2 + all_ands
stn_notall = len(compare_stn) - counter1 - counter2 + all_ands
#%% plot venn2
# Use the venn2 function
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 15))
out = venn2(
    subsets=(
        len(attractor_space_pd) - counter,
        len(attractor_space_h) - counter,
        counter,
    ),
    set_labels=("PD", "Healthy"),
    alpha=0.7,
    ax=ax1,
)
for text in out.set_labels:
    text.set_fontsize(36)

for text in out.subset_labels:
    text.set_fontsize(36)
# out.get_label_by_id('10').set_text('85131\n53 attr')
out.get_patch_by_id("10").set_color("#ee6c4d")
out.get_patch_by_id("11").set_color("#e0fbfc")
out.get_patch_by_id("01").set_color("#98c1d9")
ax1.set_title("Number of attractors", size=38)


labels = ["PD", "Healthy"]
com = [
    np.sum(overlap1) / np.sum(attractor_counts_pd),
    np.sum(overlap) / np.sum(attractor_counts_h),
]
un = [
    1 - np.sum(overlap1) / np.sum(attractor_counts_pd),
    1 - np.sum(overlap) / np.sum(attractor_counts_h),
]

width = 0.35  # the width of the bars: can also be len(x) sequence

barlist1 = ax2.bar(labels, com, width, label="Common", alpha=0.7)
barlist2 = ax2.bar(labels, un, width, bottom=com, label="Unique", alpha=0.7)
barlist1[0].set_color("#e0fbfc")
barlist1[1].set_color("#e0fbfc")
barlist2[0].set_color("#ee6c4d")
barlist2[1].set_color("#98c1d9")

ax2.set_ylabel("Fraction", fontsize=34)
ax2.tick_params(axis="x", labelsize=34)
ax2.tick_params(axis="y", labelsize=34)
ax2.set_title("Basins of attraction", size=36)

(m1,) = ax2.plot(
    [],
    [],
    c="#ee6c4d",
    marker="s",
    markersize=38,
    fillstyle="left",
    linestyle="none",
    markeredgecolor="black",
    alpha=0.7,
)

(m2,) = ax2.plot(
    [],
    [],
    c="#98c1d9",
    marker="s",
    markersize=38,
    fillstyle="right",
    linestyle="none",
    markeredgecolor="black",
    alpha=0.7,
)

# ---- Define Second Legend Entry ----

(m3,) = ax2.plot(
    [],
    [],
    c="#e0fbfc",
    marker="s",
    markersize=38,
    linestyle="none",
    markeredgecolor="black",
    alpha=0.7,
)

# ---- Plot Legend ----

ax2.legend(
    ((m2, m1), (m3)), ("Unique", "Common"), numpoints=1, labelspacing=2, fontsize=24
)


plt.suptitle("Healthy and PD", fontsize=38, weight='bold')
fig.tight_layout()
# plt.savefig(f'Animations/venn2.pdf', dpi=600,transparent=True)
plt.show()
#%% venn
# Use the venn3 function
fig, (ax1,ax2) = plt.subplots(1, 2, figsize=(23, 15))
out = venn3(
    subsets=(
        pd_notall,
        h_notall,
        h_and_pd_notall,
        stn_notall,
        pd_and_stn_notall,
        h_and_stn_notall,
        all_ands,
    ),
    set_labels=("PD", "Healthy", "STN+SNr DBS"),
    alpha=0.7,
    ax=ax1,
)
for text in out.set_labels:
    text.set_fontsize(38)

for text in out.subset_labels:
    text.set_fontsize(38)
# out.get_label_by_id('10').set_text('85131\n53 attr')
out.get_patch_by_id("10").set_color("#ee6c4d")
out.get_patch_by_id("11").set_color("#e0fbfc")
out.get_patch_by_id("01").set_color("#98c1d9")
out.get_patch_by_id("101").set_color("#3d5a80")
out.get_patch_by_id("001").set_color("#ffb703")
ax1.set_title("Number of period-3 limit cycles", size=38)

labels = ["PD", "Healthy", "STN+SNr DBS"]
alls = [
    np.sum(overlap6) / np.sum(attractor_counts_pd),
    np.sum(overlap7) / np.sum(attractor_counts_h),
    np.sum(overlap8) / np.sum(now_dbs_counts),
]
un = [
    1 - (np.sum(overlap6) + (np.sum(overlap1) - np.sum(overlap6)) + (np.sum(overlap4) - np.sum(overlap6))) / np.sum(attractor_counts_pd),
    1 - (np.sum(overlap7) + (np.sum(overlap) - np.sum(overlap7)) + (np.sum(overlap2) - np.sum(overlap7))) / np.sum(attractor_counts_h),
    1 - (np.sum(overlap8) + (np.sum(overlap5) - np.sum(overlap8)) + (np.sum(overlap3) - np.sum(overlap8))) / np.sum(now_dbs_counts),
]
with1 = [
    (np.sum(overlap1) - np.sum(overlap6)) / np.sum(attractor_counts_pd),
    (np.sum(overlap) - np.sum(overlap7)) / np.sum(attractor_counts_h),
    (np.sum(overlap5) - np.sum(overlap8)) / np.sum(now_dbs_counts) #pd and stn
]
with2 = [
    (np.sum(overlap4) - np.sum(overlap6)) / np.sum(attractor_counts_pd), #pd and stn
    (np.sum(overlap2) - np.sum(overlap7)) / np.sum(attractor_counts_h),
    (np.sum(overlap3) - np.sum(overlap8)) / np.sum(now_dbs_counts) #h and stn
]

width = 0.35  # the width of the bars: can also be len(x) sequence

barlist1 = ax2.bar(labels, alls, width, label="Common", alpha=0.7)
barlist2 = ax2.bar(labels, with1, width, bottom=alls, label="with1", alpha=0.7)
barlist3 = ax2.bar(labels, with2, width, bottom=np.array(with1)+np.array(alls), label='with2',alpha=0.7)
barlist4 = ax2.bar(labels, un, width, bottom=np.array(with2)+np.array(alls)+np.array(with1), label='Unique',alpha=0.7)
barlist1[0].set_color("#653265")
barlist1[1].set_color("#653265")
barlist1[2].set_color("#653265")
barlist4[0].set_color("#ee6c4d")
barlist4[1].set_color("#98c1d9")
barlist4[2].set_color("#ffb703")
barlist2[0].set_color("#e0fbfc")
barlist2[1].set_color("#e0fbfc")
barlist2[2].set_color("#3d5a80")
barlist3[0].set_color("#3d5a80")
barlist3[1].set_color("#0058b3")
barlist3[2].set_color("#0058b3")

ax2.set_ylabel("Fraction", fontsize=34)
ax2.tick_params(axis="x", labelsize=34)
ax2.tick_params(axis="y", labelsize=34)
ax2.spines['right'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax2.set_title("Basins of attraction", size=38)

plt.suptitle("Healthy, PD and STN+SNr DBS", fontsize=38,fontweight="bold")
#fig.tight_layout()
plt.savefig(f'Animations/venn3_stn_upd1.pdf', dpi=600,transparent=True)
plt.show()

#%% calculate coactivation matrices
coact_h = coact(h[indd_h])
coact_pd = coact(pd[indd_pd])
coact_stn = coact(stn[indd_stn])
coact_ssnr = coact(ssnr[indd_ssnr])

#%% plot coactivation matrices
import seaborn as sns
import matplotlib.pylab as plt
from matplotlib import pyplot

plot_state = [
    "LC",
    "PRF",
    "CNF",
    "PPN",
    "SNr",
    "STN",
    "GPi",
    "GPe",
    "Str",
    "Ctx",
    "SNc",
    "Th",
]
figure = pyplot.figure()
ax = sns.heatmap(
    coact_h,
    cbar_kws={"label": "Coactivation strength"},
    xticklabels=plot_state,
    yticklabels=plot_state,
cmap="Reds").set_title("Coactivation matrix, healthy")
plt.ylabel("Region")
plt.xlabel("Region")
plt.show()

figure = pyplot.figure()
ax = sns.heatmap(
    coact_pd,
    cbar_kws={"label": "Coactivation strength"},
    xticklabels=plot_state,
    yticklabels=plot_state,
cmap="Reds").set_title("Coactivation matrix, PD")
plt.ylabel("Region")
plt.xlabel("Region")
plt.show()

figure = pyplot.figure()
ax = sns.heatmap(
    coact_stn,
    cbar_kws={"label": "Coactivation strength"},
    xticklabels=plot_state,
    yticklabels=plot_state,
).set_title("Coactivation matrix, STN-DBS")
plt.ylabel("Region")
plt.xlabel("Region")
plt.show()

figure = pyplot.figure()
ax = sns.heatmap(
    coact_ssnr,
    cbar_kws={"label": "Coactivation strength"},
    xticklabels=plot_state,
    yticklabels=plot_state,
).set_title("Coactivation matrix, STN+SNr DBS")
plt.ylabel("Region")
plt.xlabel("Region")
plt.show()

#%% Re-order FC to get modules visible
import bct
from netneurotools import plotting

tr = 0.6

h_cl = coact_h.astype(np.float64)

ci, Q = bct.community_louvain(h_cl, gamma=tr)
num_ci = len(np.unique(ci))
print(ci)
print('For healthy state: {} clusters detected with a modularity of {:.2f}.'.format(num_ci, Q))

fig, ax1 = plt.subplots(figsize=(20, 15))
ax1=plotting.plot_mod_heatmap(h_cl, ci, cmap='rocket',xticklabels=plot_state, yticklabels=plot_state,mask_diagonal=False,square=False,edgecolor=(0, 0, 0, 0))
ax1.set_title('Coactivation matrix, healthy',fontweight="bold")
#fig.tight_layout()
plt.savefig(f'Animations/try.pdf', dpi=600,transparent=True)
plt.show()

pd_cl = coact_pd.astype(np.float64)

ci, Q = bct.community_louvain(pd_cl, gamma=tr)
num_ci = len(np.unique(ci))
print(ci)
print('For PD state: {} clusters detected with a modularity of {:.2f}.'.format(num_ci, Q))

fig, ax1 = plt.subplots(figsize=(20, 15))
ax1 = plotting.plot_mod_heatmap(pd_cl, ci, cmap='rocket',xticklabels=plot_state, yticklabels=plot_state,mask_diagonal=False,square=False,edgecolor=(0, 0, 0, 0))
ax1.set_title('Coactivation matrix, PD',fontweight="bold")
plt.savefig(f'Animations/try1.pdf', dpi=600,transparent=True)
plt.show()

stn_cl = coact_stn.astype(np.float64)

ci, Q = bct.community_louvain(stn_cl, gamma=tr)
num_ci = len(np.unique(ci))
print(ci)
print('For STN-DBS state: {} clusters detected with a modularity of {:.2f}.'.format(num_ci, Q))

fig, ax1 = plt.subplots(figsize=(20, 15))
ax1 = plotting.plot_mod_heatmap(stn_cl, ci, cmap='rocket',xticklabels=plot_state, yticklabels=plot_state,mask_diagonal=False,square=False,edgecolor=(0, 0, 0, 0))
ax1.set_title('Coactivation matrix, STN DBS',fontweight="bold")
plt.savefig(f'Animations/try2.pdf', dpi=600,transparent=True)
plt.show()

ssnr_cl = coact_ssnr.astype(np.float64)

ci, Q = bct.community_louvain(ssnr_cl, gamma=tr)
num_ci = len(np.unique(ci))
print(ci)
print('For STN+SNr-DBS state: {} clusters detected with a modularity of {:.2f}.'.format(num_ci, Q))

fig, ax1 = plt.subplots(figsize=(20, 15))
ax1 = plotting.plot_mod_heatmap(ssnr_cl, ci, cmap='rocket',xticklabels=plot_state, yticklabels=plot_state,mask_diagonal=False,square=False,edgecolor=(0, 0, 0, 0))
ax1.set_title('Coactivation matrix, STN+SNr DBS',fontweight="bold")
plt.savefig(f'Animations/try3.pdf', dpi=600,transparent=True)
plt.show()
#%% Calculate distances between network configurations

l_h_stn = np.mean(np.abs(coact_h - coact_stn))
l_pd_stn = np.mean(np.abs(coact_pd - coact_stn))

l_h_ssnr = np.mean(np.abs(coact_h - coact_ssnr))
l_pd_ssnr = np.mean(np.abs(coact_pd - coact_ssnr))

borderline = np.mean(np.abs(coact_h - coact_pd))

# distances plot
plot_state1 = ["PD", "STN", "STN+SNr"]

dif_h = [borderline, l_h_stn, l_h_ssnr]

dif_pd = [l_pd_stn, l_pd_ssnr]

fig = plt.figure(figsize=(15, 10))
# plt.plot(plot_state, dif_pd, label='Distance to PD',
#         marker = 'D')
plt.bar(plot_state1, dif_h, label="Distance to healthy", color="#d35f5f", width=0.5)
plt.ylim(0)
plt.xlabel("Stimulation sites")
plt.ylabel("Distance, a.u.")
plt.title("Distances between network configurations", fontweight="bold")
plt.legend(loc="lower left")
fig.tight_layout()
# plt.savefig(f'Animations/dist1.pdf', dpi=600,transparent=True)
plt.show()

#%% Calculate activity propagation matrix
# for excitatory connections
coact_h_sh = coact_sh(h[indd_h])
coact_pd_sh = coact_sh(pd[indd_pd])
coact_stn_sh = coact_sh(stn[indd_stn])
coact_ssnr_sh = coact_sh(ssnr[indd_ssnr])

# distances shifted
h_stn_del = np.abs(coact_h_sh - coact_stn_sh)

h_del = np.abs(coact_h_sh - coact_ssnr_sh)

borderline_del = np.abs(coact_h_sh - coact_pd_sh)

# for inhibitory connections
coact_h_40 = coact40(h[indd_h])
coact_pd_40 = coact40(pd[indd_pd])
coact_stn_40 = coact40(stn[indd_stn])
coact_ssnr_40 = coact40(ssnr[indd_ssnr])

# distances shifted
h_stn_del40 = np.abs(coact_h_40 - coact_stn_40)

h_del40 = np.abs(coact_h_40 - coact_ssnr_40)

borderline_del40 = np.abs(coact_h_40 - coact_pd_40)
#%% projection graphs
mn = A1.astype(np.float64)
mn2 = A1.astype(np.float64)

for i in range(len(h_del)):
    for j in range(len(h_del)):
        if h_del[i, j] <= borderline_del[i, j]:
            if h_stn_del[i, j] <= borderline_del[i, j]:
                mn[i, j] = 1
            else:
                mn[i, j] = 2
        else:
            if h_stn_del[i, j] <= borderline_del[i, j]:
                mn[i, j] = 3
            else:
                mn[i, j] = 4

for i in range(len(h_del40)):
    for j in range(len(h_del40)):
        if h_del40[i, j] <= borderline_del40[i, j]:
            if h_stn_del40[i, j] <= borderline_del40[i, j]:
                mn2[i, j] = 1
            else:
                mn2[i, j] = 2
        else:
            if h_stn_del40[i, j] <= borderline_del40[i, j]:
                mn2[i, j] = 3
            else:
                mn2[i, j] = 4

mn1 = mn.astype(np.float64)
mn3 = mn2.astype(np.float64)

for i in range(len(A1)):
    for j in range(len(A1)):
        if A1[i, j] != 1:
            mn1[i, j] = None

for i in range(len(A1)):
    for j in range(len(A1)):
        if A1[i, j] != -1:
            mn3[i, j] = None

ac_prop = np.nansum(np.dstack((mn3, mn1)), 2)
ac_prop[ac_prop == 0] = None

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

figure = pyplot.figure()
ax = sns.heatmap(
    ac_prop,
    cbar_kws={"label": "Property"},
    xticklabels=plot_state,
    yticklabels=plot_state,
    cmap=plt.get_cmap("Dark2", 4),
    vmin=1,
    vmax=4,
    linewidth=0.5,
    square=True,
    cbar=False,
)  # .set_title("Distance to healthy")
plt.ylabel("Region")
plt.xlabel("Region state on the next step")
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.1)
cbar = plt.colorbar(ax.collections[0], cax=cax)
cbar.set_ticks([1.5, 2.25, 3, 3.75])
cbar.ax.set_yticklabels(
    [
        "STN- and STN+SNr-DBS \n are closer to \n the healthy state",
        "STN+SNr-DBS is closer \n to the healthy state",
        "STN-DBS is closer \n to the healthy state",
        "STN- and STN+SNr-DBS \n are further from \n the healthy state",
    ],
    size=10,
)
cbar.ax.tick_params(axis="y", which="major", length=0, pad=15)
# cbar.outline.set_edgecolor('black')
# cbar.outline.set_linewidth(2)
ax.set_title("Distance to healthy")
plt.tight_layout()
plt.show()
#%% For the frequency plot in supp
#frequency
h_freq = np.sum(np.sum(h[:,:,:]==1,axis=2),axis=0)/((3**12)*100)
pd_freq = np.sum(np.sum(pd[:,:,:]==1,axis=2),axis=0)/((3**12)*100)
stn_freq = np.sum(np.sum(stn[:,:,:]==1,axis=2),axis=0)/((3**12)*100)
ssnr_freq = np.sum(np.sum(ssnr[:,:,:]==1,axis=2),axis=0)/((3**12)*100)

#frequency limit cycles
h_freq_lc = np.sum(np.sum(h[indd_h,:,:]==1,axis=2),axis=0)/((len(indd_h))*100)
pd_freq_lc = np.sum(np.sum(pd[indd_pd,:,:]==1,axis=2),axis=0)/((len(indd_pd))*100)
stn_freq_lc = np.sum(np.sum(stn[indd_stn,:,:]==1,axis=2),axis=0)/((len(indd_stn))*100)
ssnr_freq_lc = np.sum(np.sum(ssnr[indd_ssnr,:,:]==1,axis=2),axis=0)/((len(indd_ssnr))*100)

#%% figs

figure = pyplot.figure(figsize=(15, 10))
plt.axhline(y=0, color='black', linestyle='dashdot', linewidth=5, label='Threshold')
plt.plot(plot_state, np.sum(A1, axis=0),label='Healthy', c="#98c1d9", linewidth=7)
plt.plot(plot_state, np.sum(A2, axis=0),label='PD',c="#ee6c4d", linewidth=7)
plt.plot(plot_state, np.sum(adj_stn.T, axis=0),label='STN DBS',c='#e6ab02', linewidth=7)
plt.plot(plot_state, np.sum(adj_ssnr.T, axis=0),label='STN+SNr DBS',c="#7570b3", linewidth=7)
plt.xlabel("Region",fontsize=34)
plt.ylabel("Effective degree",fontsize=34)
plt.legend(loc="lower left")
plt.tight_layout()
#plt.title('multiple plots')
plt.savefig(f'Animations/ef_def.pdf', dpi=600,transparent=True)
plt.show()

figure = pyplot.figure(figsize=(15, 10))
plt.plot(plot_state, h_freq, label='Healthy', c="#98c1d9", linewidth=7)
plt.plot(plot_state, pd_freq, label='PD',c="#ee6c4d", linewidth=7)
plt.plot(plot_state, stn_freq, label='STN DBS',c='#e6ab02', linewidth=7)
plt.plot(plot_state, ssnr_freq, label='STN+SNr DBS',c="#7570b3", linewidth=7)
plt.xlabel("Region",fontsize=34)
plt.ylabel("Excitation frequency",fontsize=34)
plt.legend(loc="lower left")
plt.tight_layout()
#plt.title('multiple plots')
plt.savefig(f'Animations/freq.pdf', dpi=600,transparent=True)
plt.show()

figure = pyplot.figure(figsize=(15, 10))
plt.plot(plot_state, h_freq_lc, label='Healthy', c="#98c1d9",linewidth=7)
plt.plot(plot_state, pd_freq_lc, label='PD',c="#ee6c4d",linewidth=7)
plt.plot(plot_state, stn_freq_lc, label='STN DBS',c='#e6ab02',linewidth=7)
plt.plot(plot_state, ssnr_freq_lc, label='STN+SNr DBS',c="#7570b3",linewidth=7)
plt.xlabel("Region",fontsize=34)
plt.ylabel("Excitation frequency, limit cycles",fontsize=34)
plt.legend(loc="lower left")
plt.tight_layout()
#plt.title('multiple plots')
plt.savefig(f'Animations/freq_lm.pdf', dpi=600,transparent=True)
plt.show()